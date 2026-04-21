
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

def simple_test():
    api_key = os.getenv("GOOGLE_API_KEY")
    print(f"API Key: {api_key[:5]}...{api_key[-5:]}")
    
    client = genai.Client(api_key=api_key)
    
    print("\n--- 1. List Models (First 5) ---")
    try:
        models = list(client.models.list())
        for m in models[:5]:
            print(f"- {m.name}")
        print(f"(Total {len(models)} models found)")
    except Exception as e:
        print(f"ERROR listing models: {e}")

    print("\n--- 2. Generate Text (gemini-2.0-flash-exp) ---")
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents="Hello, are you working?"
        )
        print(f"RESPONSE: {response.text}")
    except Exception as e:
        print(f"ERROR with gemini-2.0-flash-exp: {e}")

    print("\n--- 3. Generate Text (gemini-1.5-flash) ---")
    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents="Hello, are you working?"
        )
        print(f"RESPONSE: {response.text}")
    except Exception as e:
        print(f"ERROR with gemini-1.5-flash: {e}")

if __name__ == "__main__":
    simple_test()
