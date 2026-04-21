
import asyncio
import logging
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트 경로 추가
sys.path.append(str(Path(__file__).resolve().parent))

from congen.pipeline import VideoGenerationPipeline
from congen.models.script import Script
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
    print("🎬 ConGen: Force Assembly")
    print("="*60)
    
    # Target specific directory
    target_dir_name = "20251216_165148_ConGen_프로젝트_소개_교육_영상을_자동으로_생성하"
    output_dir = settings.OUTPUT_DIR / target_dir_name
    
    if not output_dir.exists():
        print(f"❌ Directory not found: {output_dir}")
        return

    print(f"📂 Target Directory: {output_dir}")
    
    # Load script
    script_path = output_dir / "1_script.json"
    if not script_path.exists():
        print("❌ Script file not found.")
        return
        
    with open(script_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        script = Script(**data)
    
    pipeline = VideoGenerationPipeline()
    
    try:
        await pipeline._assemble_final_video(script, output_dir)
        print(f"\n✅ Assembly completed successfully!")
    except Exception as e:
        print(f"\n❌ Assembly failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())
