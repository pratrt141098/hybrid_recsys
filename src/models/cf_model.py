import implicit
import scipy.sparse as sparse
import pandas as pd
import numpy as np
import os
from sqlalchemy import create_engine

# Config
DB_URL = "postgresql://admin:password@localhost:5435/recsys_db"
MODEL_DIR = "data/models/"

class CollaborativeFilter:
    def __init__(self):
        # Initialize empty model
        self.model = implicit.als.AlternatingLeastSquares(
            factors=50, regularization=0.01, iterations=15
        )
        self.user_map = {}
        self.item_map = {}
        self.rev_item_map = {}
        self.user_items_matrix = None

    def train(self):
        print("Loading data from DB...")
        engine = create_engine(DB_URL)
        query = """
            SELECT user_id, product_id, 
            CASE 
                WHEN event_type = 'purchase' THEN 10 
                WHEN event_type = 'cart' THEN 5 
                ELSE 1 
            END as weight
            FROM events
        """
        df = pd.read_sql(query, engine)
        
        # Mappings
        unique_users = df['user_id'].unique()
        unique_items = df['product_id'].unique()
        
        self.user_map = {id: i for i, id in enumerate(unique_users)}
        self.item_map = {id: i for i, id in enumerate(unique_items)}
        self.rev_item_map = {i: id for id, i in self.item_map.items()}
        
        # Matrix
        user_inds = [self.user_map[u] for u in df['user_id']]
        item_inds = [self.item_map[i] for i in df['product_id']]
        
        self.user_items_matrix = sparse.csr_matrix(
            (df['weight'], (item_inds, user_inds)), 
            shape=(len(unique_items), len(unique_users))
        )
        
        print(f"Training on {len(df)} interactions...")
        self.model.fit(self.user_items_matrix)
        print("Training complete.")

    def recommend(self, user_id, n=10):
        if user_id not in self.user_map:
            return []
        user_idx = self.user_map[user_id]
        ids, scores = self.model.recommend(user_idx, self.user_items_matrix[user_idx], N=n)
        return [int(self.rev_item_map[i]) for i in ids]
    
    def save(self):
        os.makedirs(MODEL_DIR, exist_ok=True)
        
        # Save Model Factors (Numpy)
        np.savez(os.path.join(MODEL_DIR, "model_factors.npz"), 
                 user_factors=self.model.user_factors, 
                 item_factors=self.model.item_factors)
        
        # Save Mappings (Numpy/Pickle is okay for dicts)
        np.save(os.path.join(MODEL_DIR, "mappings.npy"), {
            'user_map': self.user_map,
            'item_map': self.item_map,
            'rev_item_map': self.rev_item_map
        }, allow_pickle=True)
        
        # Save Interaction Matrix
        sparse.save_npz(os.path.join(MODEL_DIR, "interactions.npz"), self.user_items_matrix)
        print(f"Model saved to {MODEL_DIR}")

    def load(self):
        print(f"Loading model from {MODEL_DIR}...")
        
        # Load Factors
        factors = np.load(os.path.join(MODEL_DIR, "model_factors.npz"))
        self.model.user_factors = factors['user_factors']
        self.model.item_factors = factors['item_factors']
        
        # Load Mappings
        mappings = np.load(os.path.join(MODEL_DIR, "mappings.npy"), allow_pickle=True).item()
        self.user_map = mappings['user_map']
        self.item_map = mappings['item_map']
        self.rev_item_map = mappings['rev_item_map']
        
        # Load Matrix
        self.user_items_matrix = sparse.load_npz(os.path.join(MODEL_DIR, "interactions.npz"))
        print("Model loaded.")

if __name__ == "__main__":
    cf = CollaborativeFilter()
    cf.train()
    cf.save()
