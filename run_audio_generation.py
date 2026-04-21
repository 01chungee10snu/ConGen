
import asyncio
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

from congen.agents.audio_generator import AudioGeneratorAgent

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    load_dotenv()
    
    print("\n" + "="*60)
    print("🔊 ConGen: Audio Generation (ElevenLabs)")
    print("="*60)
    
    # 가장 최근 결과 폴더 찾기
    output_root = Path(__file__).resolve().parent / "output"
    dirs = sorted([d for d in output_root.iterdir() if d.is_dir()], key=lambda x: x.stat().st_mtime, reverse=True)
    
    if not dirs:
        print("❌ No result folders found.")
        return
    
    latest_dir = dirs[0]
    print(f"📂 Target Directory: {latest_dir}")
    
    # 스크립트 로드
    script_path = latest_dir / "1_script.json"
    if not script_path.exists():
        print("❌ Script file not found.")
        return
    
    with open(script_path, "r", encoding="utf-8") as f:
        script_data = json.load(f)
    
    # 오디오 출력 디렉토리
    audio_dir = latest_dir / "3_audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    
    # 에이전트 초기화 (ElevenLabs)
    agent = AudioGeneratorAgent()
    
    scenes = script_data.get("scenes", [])
    print(f"📝 Found {len(scenes)} scenes")
    
    for scene in scenes:
        scene_id = scene.get("scene_id", 0)
        
        # audio.narration 접근
        audio_data = scene.get("audio", {})
        narration = audio_data.get("narration", "")
        
        if not narration:
            print(f"⚠️ Scene {scene_id}: No narration, skipping.")
            continue
        
        output_path = audio_dir / f"scene_{scene_id:03d}.mp3"
        
        print(f"\n🎙️ Scene {scene_id}: Generating audio...")
        print(f"   Text: {narration[:50]}...")
        
        try:
            result = await agent.run(narration, output_path)
            print(f"   ✅ Saved: {result}")
        except Exception as e:
            print(f"   ❌ Failed: {e}")
    
    print(f"\n🎉 Audio generation completed! Files in: {audio_dir}")

if __name__ == "__main__":
    asyncio.run(main())
