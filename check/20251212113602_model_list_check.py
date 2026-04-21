
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

def list_all_models():
    api_key = os.getenv("GOOGLE_API_KEY")
    client = genai.Client(api_key=api_key)
    
    print("\n--- Available Models ---")
    try:
        models = list(client.models.list())
        for m in models:
            # 이미지나 비디오 관련 모델, 또는 최신 gemini 모델만 필터링
            name = m.name.lower()
            if any(k in name for k in ['gemini', 'veo', 'imagen', 'video', 'image']):
                print(f"- {m.name}")
                
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    list_all_models()
