
import asyncio
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트 경로 추가
sys.path.append(str(Path(__file__).resolve().parent))

from congen.pipeline import VideoGenerationPipeline
from congen.config.settings import settings

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
    print("🔄 ConGen: Resuming Pipeline")
    print("="*60)
    
    # 가장 최근의 output 디렉토리 찾기
    output_root = settings.OUTPUT_DIR
    if not output_root.exists():
        print("❌ No output directory found.")
        return

    # 날짜순 정렬하여 가장 최근 폴더 선택
    subdirs = [d for d in output_root.iterdir() if d.is_dir()]
    if not subdirs:
        print("❌ No project directories found in output.")
        return
        
    latest_dir = sorted(subdirs, key=lambda x: x.name, reverse=True)[0]
    print(f"📂 Target Directory: {latest_dir}")
    
    pipeline = VideoGenerationPipeline()
    
    try:
        await pipeline.run_from_existing(latest_dir)
        print(f"\n✅ Resume completed successfully!")
    except Exception as e:
        print(f"\n❌ Resume failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())
