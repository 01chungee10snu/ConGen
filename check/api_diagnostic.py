
import os
import asyncio
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pathlib import Path

async def check_api():
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    client = genai.Client(api_key=api_key)
    
    print("🔍 API Key Connectivity Check...")
    
    # 1. Gemini 텍스트 생성 테스트
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents="Hello, say 'API is working!'"
        )
        print(f"✅ [Gemini 2.0 Flash]: Success! ({response.text.strip()})")
    except Exception as e:
        print(f"❌ [Gemini 2.0 Flash]: Failed - {e}")

    # 2. Nano Banana Pro (이미지) 테스트
    try:
        # 가벼운 이미지 생성 요청 (Gemini 3 Pro Image)
        # 실제 생성은 비용이 발생하므로 모델 존재 여부와 간단한 요청 가능성 확인
        response = client.models.generate_content(
            model="gemini-3-pro-image-preview",
            contents="Generate a simple blue circle icon.",
            config=types.GenerateContentConfig(
                # 이미지 생성 시 필요한 모달리티 확인
            )
        )
        print(f"✅ [Nano Banana Pro]: Model is accessible.")
    except Exception as e:
        print(f"❌ [Nano Banana Pro]: Failed or No Access - {e}")

    # 3. Veo 3.1 (비디오) 테스트
    try:
        # 모델 리스트에서 Veo가 있는지 확인 (실제 비디오 생성은 매우 비싸므로 리스트 확인 위주)
        models = client.models.list()
        veo_found = any("veo" in m.name.lower() for m in models)
        if veo_found:
            print(f"✅ [Veo 3.1]: Veo models found in your project.")
        else:
            print(f"⚠️ [Veo 3.1]: Veo model NOT found in list. (May need special access)")
    except Exception as e:
        print(f"❌ [Veo API Access]: Failed to list models - {e}")

if __name__ == "__main__":
    asyncio.run(check_api())
