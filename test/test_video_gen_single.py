
import asyncio
import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from congen.agents.video_generator import VideoGeneratorAgent

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    # .env 로드
    load_dotenv(override=True)
    
    logger.info("🎬 Starting single video generation test...")
    
    # 에이전트 초기화
    agent = VideoGeneratorAgent()
    
    # 테스트용 이미지 및 프롬프트 설정
    # 주의: 실제 존재하는 이미지 경로여야 함
    image_path = Path(r"c:\Github\ConGen\output\20251212_134452_통계_기초_평균_분산_표준편차에_대해_직관적으로_이해할\2_scenes\scene_001.png")
    prompt = "A clean, minimalist 3D animation showing chaotic floating numbers (1, 5, 8, 3, 9) slowly settling down onto a straight horizontal line. The line glows softly, representing the 'Mean' (Average). The background is a soft, gradient blue. Cinematic lighting."
    output_path = Path(r"c:\Github\ConGen\test_output_video.mp4")
    
    if not image_path.exists():
        logger.error(f"❌ Image file not found: {image_path}")
        return

    try:
        logger.info(f"Using API Key: {os.getenv('GOOGLE_API_KEY')[:10]}...")
        result = await agent.run(prompt, image_path, output_path)
        logger.info(f"✅ Test successful! Video saved to: {result}")
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
