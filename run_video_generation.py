
import asyncio
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트 경로 추가
sys.path.append(str(Path(__file__).resolve().parent))

from congen.pipeline import VideoGenerationPipeline

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("video_gen.log", encoding="utf-8")
    ]
)

async def main():
    print("\n" + "="*60)
    print("🎥 ConGen: Video Generation (Veo 3.1)")
    print("="*60)
    
    # 가장 최근 결과 폴더 찾기
    output_root = Path(__file__).resolve().parent / "output"
    if not output_root.exists():
        print("❌ No output directory found.")
        return
        
    dirs = sorted([d for d in output_root.iterdir() if d.is_dir()], key=lambda x: x.stat().st_mtime, reverse=True)
    if not dirs:
        print("❌ No result folders found.")
        return
        
    latest_dir = dirs[0]
    print(f"📂 Target Directory: {latest_dir}")
    
    pipeline = VideoGenerationPipeline()
    
    try:
        await pipeline.run_from_existing(latest_dir)
        print(f"\n✅ Video generation completed successfully!")
    except Exception as e:
        print(f"\n❌ Video generation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())
