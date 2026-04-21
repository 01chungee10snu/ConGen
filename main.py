
import asyncio
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트 경로 추가 (필요시)
sys.path.append(str(Path(__file__).resolve().parent))

from congen.pipeline import VideoGenerationPipeline

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("pipeline.log", encoding="utf-8")
    ]
)

async def main():
    print("\n" + "="*60)
    print("🚀 ConGen: Educational Video Generation Framework")
    print("="*60)
    
    topic = "ConGen 프로젝트 소개: 교육 영상을 자동으로 생성하는 AI 에이전트 프레임워크 (총 10개 씬으로 구성)"
    print(f"📝 Topic: {topic}")
    
    pipeline = VideoGenerationPipeline()
    
    try:
        output_dir = await pipeline.run(topic)
        print(f"\n✅ All tasks completed successfully!")
        print(f"📂 Output Directory: {output_dir}")
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())
