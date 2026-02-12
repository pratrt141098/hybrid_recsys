from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import pickle
# from sqlalchemy import create_engine  # Disabled for Render demo
from src.models.llm_ranker import LLMRanker
# IMPORTANT: Import the class so pickle knows about it
from src.models.cf_model import CollaborativeFilter
from dotenv import load_dotenv
import os

load_dotenv()

# Global variables
cf_model = None
engine = None
llm_ranker = None

# Initialize App
app = FastAPI(title="Hybrid RecSys API")

# --- Startup Event ---
@app.on_event("startup")
def load_resources():
    global cf_model, engine, llm_ranker
    print("Loading resources...")

    # 1. Database (Disabled for Render Demo)
    # DB_URL = "postgresql://admin:password@localhost:5435/recsys_db"
    # engine = create_engine(DB_URL)
    
    # 2. Model
    try:
        cf_model = CollaborativeFilter()
        cf_model.load()
        print("ALS Model loaded successfully.")
    except Exception as e:
        print(f"Error loading model: {e}")
        cf_model = None

    # 3. LLM Ranker
    # Ensure GEMINI_API_KEY is set in Render Environment Variables
    try:
        llm_ranker = LLMRanker(model_name="gemini-1.5-flash")
        print("LLM Ranker initialized.")
    except Exception as e:
        print(f"Error initializing LLM Ranker: {e}")
        llm_ranker = None

# --- Schemas ---
class RecommendRequest(BaseModel):
    user_id: int
    n_candidates: int = 10
    use_llm: bool = True

# --- Helpers (Dummy Data for Demo) ---
def get_product_metadata(product_ids):
    """Returns dummy product names for demo purposes."""
    if not product_ids:
        return []
    
    # Flatten if needed
    if isinstance(product_ids[0], (list, tuple)):
        product_ids = [p[0] for p in product_ids]
    
    # Dummy data logic
    return [{"id": int(pid), "name": f"Product #{pid} (Demo)"} for pid in product_ids]

def get_user_profile(user_id):
    """Returns dummy user profile for demo purposes."""
    return {
        "persona": "Tech Enthusiast (Demo)",
        "recent_views": "Gaming Laptop, Wireless Mouse, Mechanical Keyboard"
    }

# --- Endpoints ---
@app.get("/")
def health_check():
    return {"status": "healthy", "model_loaded": cf_model is not None}

@app.post("/recommend")
def recommend(req: RecommendRequest):
    if not cf_model:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        # 1. Fast Retrieval (ALS)
        # If model fails, fallback to dummy IDs
        try:
            candidate_ids = cf_model.recommend(req.user_id, n=req.n_candidates)
        except Exception as e:
            print(f"ALS Inference Error: {e}")
            candidate_ids = [101, 102, 103, 104, 105]

        # 2. Fetch Metadata (Dummy)
        candidates = get_product_metadata(candidate_ids)

        # 3. Re-Ranking (LLM)
        if req.use_llm and candidates and llm_ranker:
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

    except Exception as e:
        # Catch-all for 500 errors to help debugging
        raise HTTPException(status_code=500, detail=str(e))
