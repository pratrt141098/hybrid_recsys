from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import pickle
from sqlalchemy import create_engine
from src.models.llm_ranker import LLMRanker
# IMPORTANT: Import the class so pickle knows about it
from src.models.cf_model import CollaborativeFilter 
from dotenv import load_dotenv
load_dotenv()  # <--- This loads the .env file


# Global variables
cf_model = None
engine = None
llm_ranker = None

# Initialize App
app = FastAPI(title="Hybrid RecSys API")

# --- Startup Event (Load Model Here) ---
# --- Startup Event ---
@app.on_event("startup")
def load_resources():
    global cf_model, engine, llm_ranker
    print("Loading resources...")
    
    # 1. Database
    DB_URL = "postgresql://admin:password@localhost:5435/recsys_db"
    engine = create_engine(DB_URL)
    
    # 2. Model (Using our new robust load method)
    try:
        cf_model = CollaborativeFilter() # Instantiate empty class
        cf_model.load()                  # Load weights from disk
        print("ALS Model loaded successfully.")
    except Exception as e:
        print(f"Error loading model: {e}")
        cf_model = None

    # 3. LLM Ranker
    llm_ranker = LLMRanker(model_name="gemini-2.5-flash")

# --- Schemas ---
class RecommendRequest(BaseModel):
    user_id: int
    n_candidates: int = 10     
    use_llm: bool = True       

# --- Helpers ---
def get_product_metadata(product_ids):
    if not product_ids:
        return []
    # Ensure product_ids is a flat list
    if isinstance(product_ids[0], (list, tuple)):
         product_ids = [p[0] for p in product_ids]
         
    query = f"SELECT product_id as id, product_name as name FROM products WHERE product_id IN ({','.join(map(str, product_ids))})"
    return pd.read_sql(query, engine).to_dict(orient="records")

def get_user_profile(user_id):
    user_query = f"SELECT persona FROM users WHERE user_id = {user_id}"
    user_df = pd.read_sql(user_query, engine)
    persona = user_df.iloc[0]['persona'] if not user_df.empty else "General Shopper"
    
    hist_query = f"""
        SELECT p.product_name 
        FROM events e 
        JOIN products p ON e.product_id = p.product_id 
        WHERE e.user_id = {user_id} AND e.event_type = 'view'
        ORDER BY e.event_time DESC LIMIT 5
    """
    hist_df = pd.read_sql(hist_query, engine)
    recent_views = ", ".join(hist_df['product_name'].tolist())
    
    return {"persona": persona, "recent_views": recent_views}

# --- Endpoints ---
@app.get("/")
def health_check():
    return {"status": "healthy", "model_loaded": cf_model is not None}

from fastapi import FastAPI, HTTPException

@app.post("/recommend")
def recommend(req: RecommendRequest):
    try:
        if not cf_model:
            raise HTTPException(status_code=503, detail="Model not loaded")

        candidate_ids = cf_model.recommend(req.user_id, n=req.n_candidates)
        candidates = get_product_metadata(candidate_ids)

        if req.use_llm and candidates:
            user_profile = get_user_profile(req.user_id)
            final_recs = llm_ranker.rerank(user_profile, candidates)
            return {
                "user_id": req.user_id,
                "strategy": "Hybrid (ALS + Gemini)",
                "profile": user_profile,
                "recommendations": final_recs,
            }
        else:
            return {
                "user_id": req.user_id,
                "strategy": "ALS Only",
                "recommendations": candidates,
            }
    except Exception as e:
        # Dev-only: expose the error so we can see it in the browser
        raise HTTPException(status_code=500, detail=str(e))


    # 1. Fast Retrieval (ALS)
    try:
        candidate_ids = cf_model.recommend(req.user_id, n=req.n_candidates)
    except Exception as e:
        print(f"ALS Error: {e}")
        candidate_ids = [1, 2, 3, 4, 5] 
    
    # 2. Fetch Metadata
    candidates = get_product_metadata(candidate_ids)
    
    # 3. Re-Ranking (LLM)
    if req.use_llm and candidates:
        user_profile = get_user_profile(req.user_id)
        final_recs = llm_ranker.rerank(user_profile, candidates)
        return {
            "user_id": req.user_id,
            "strategy": "Hybrid (ALS + Gemini)",
            "profile": user_profile,
            "recommendations": final_recs
        }
    else:
        return {
            "user_id": req.user_id, 
            "strategy": "ALS Only",
            "recommendations": candidates
        }