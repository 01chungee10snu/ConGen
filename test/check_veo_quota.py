
import os
import logging
from pathlib import Path
from google import genai
from google.genai import types
from google.genai.errors import ClientError
from congen.config.settings import settings

# 로거 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_quota():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        api_key = settings.GOOGLE_API_KEY
    
    if not api_key:
        logger.error("❌ GOOGLE_API_KEY not found.")
        return

    client = genai.Client(api_key=api_key)
    model_name = settings.MODEL_VEO
    
    # 테스트용 이미지 경로 (가장 최근 생성된 이미지 사용)
    image_path = Path(r"c:\Github\ConGen\output\20251212_134452_통계_기초_평균_분산_표준편차에_대해_직관적으로_이해할\2_scenes\scene_001.png")
    
    if not image_path.exists():
        logger.error(f"❌ Test image not found at {image_path}")
        return

    logger.info(f"🔍 Checking quota for model: {model_name}...")
    
    try:
        with open(image_path, "rb") as f:
            image_bytes = f.read()
            
        image = types.Image(image_bytes=image_bytes, mime_type="image/png")
        
        # 아주 짧은 요청 시도
        operation = client.models.generate_videos(
            model=model_name,
            prompt="Test video for quota check",
            image=image,
            config=types.GenerateVideosConfig(aspect_ratio="16:9")
        )
        
        logger.info("✅ Quota is AVAILABLE! (Operation created successfully)")
        logger.info(f"   Operation Name: {operation.name}")
        logger.info("   You can resume the pipeline now.")
        
    except ClientError as e:
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            logger.warning("⛔ Quota EXHAUSTED (429 Error). Please wait a bit longer.")
            logger.warning(f"   Details: {e}")
        else:
            logger.error(f"❌ An error occurred, but it might not be quota related: {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    check_quota()
