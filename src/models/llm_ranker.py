import os
import json
import google.generativeai as genai

class LLMRanker:
    def __init__(self, model_name="gemini-2.5-flash"):
        # Configure the API
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def rerank(self, user_profile, candidate_products):
        # Construct the same prompt as before
        prompt = f"""
        You are an AI shopping assistant. 
        User Persona: {user_profile.get('persona', 'General Shopper')}
        User Context: The user recently viewed {user_profile.get('recent_views', 'various items')}.
        
        Task: 
        1. Select the top 3 most relevant products from the Candidate List below.
        2. Write a 1-sentence explanation for EACH, addressing the user directly.
        
        Candidate List:
        {json.dumps(candidate_products)}
        
        Return ONLY valid JSON in this format:
        [
            {{"product_id": 123, "explanation": "Since you like..."}},
            ...
        ]
        """
        
        try:
            # Call Gemini
            response = self.model.generate_content(prompt)
            raw_text = response.text
            
            # --- FIX STARTS HERE ---
            # Correctly handle the list indexing [1] before splitting again
# FIXED
            if "```json" in raw_text:
                # 1. Split by header -> Get 2nd part (index 1)
                # 2. Split that part by footer -> Get 1st part (index 0)
                # 3. Strip whitespace
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].split("```")[0].strip()
                
            return json.loads(raw_text)
            
        except Exception as e:
            print(f"Gemini Error: {e}")
            # Fallback
            return [{"product_id": p['id'], "explanation": "Top pick for you."} for p in candidate_products[:3]]

