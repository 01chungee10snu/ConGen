
import sys
import asyncio
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 프로젝트 루트 경로 추가
sys.path.append(str(Path(__file__).resolve().parent.parent))

from congen.agents.image_generator import ImageGeneratorAgent
from congen.models.script import Script

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def get_latest_script_path():
    """가장 최근에 생성된 script.json 파일 경로 찾기"""
    output_dir = Path(__file__).resolve().parent.parent / "output"
    if not output_dir.exists():
        return None
        
    # 날짜순 정렬
    dirs = sorted([d for d in output_dir.iterdir() if d.is_dir()], key=lambda x: x.stat().st_mtime, reverse=True)
    
    for d in dirs:
        script_path = d / "1_script.json"
        if script_path.exists():
            return script_path
            
    return None

async def test_image_generation():
    print("\n" + "="*60)
    print("🎨 Image Generation Test")
    print("="*60)
    
    script_path = get_latest_script_path()
    if not script_path:
        print("❌ No script.json found. Please run script generation test first.")
        return

    print(f"📂 Loading script from: {script_path}")
    
    try:
        with open(script_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            script = Script(**data)
            
        agent = ImageGeneratorAgent()
        
        # 첫 번째 장면만 테스트
        scene = script.scenes[0]
        print(f"\n📸 Generating image for Scene {scene.scene_id}...")
        print(f"   Prompt: {scene.visual.description}")
        
        # 저장 경로 설정
        output_dir = script_path.parent / "2_scenes"
        output_path = output_dir / f"scene_{scene.scene_id:03d}.png"
        
        generated_path = await agent.run(scene.visual.description, output_path)
        
        print(f"\n✅ Image Generated Successfully!")
        print(f"   Path: {generated_path}")
        
    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_image_generation())
