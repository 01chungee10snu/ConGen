
import sys
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 프로젝트 루트 경로 추가
sys.path.append(str(Path(__file__).resolve().parent.parent))

from congen.agents.script_generator import ScriptGeneratorAgent

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_script_generation():
    print("\n" + "="*60)
    print("🎬 Script Generation Test")
    print("="*60)
    
    agent = ScriptGeneratorAgent()
    
    prompt = "통계 기초: 평균, 분산, 표준편차에 대해 직관적으로 이해할 수 있는 1분 교육 영상"
    print(f"📝 Prompt: {prompt}")
    
    try:
        script = await agent.run(prompt)
        
        print("\n✅ Script Generated Successfully!")
        print(f"   Title: {script.metadata.title}")
        
        # --- 결과 저장 로직 추가 ---
        from datetime import datetime
        import json
        
        # 타임스탬프 기반 폴더 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sanitized_topic = "".join(c for c in script.metadata.topic if c.isalnum() or c in (' ', '_')).strip().replace(' ', '_')
        output_dir = Path(__file__).resolve().parent.parent / "output" / f"{timestamp}_{sanitized_topic}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # JSON 파일 저장
        output_path = output_dir / "1_script.json"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(script.model_dump(), indent=2, ensure_ascii=False))
            
        print(f"\n💾 Script Saved to: {output_path}")
        # -------------------------
        
        print(f"   Scene Count: {len(script.scenes)}")
        
        print("\n📜 Scene Details:")
        for scene in script.scenes:
            print(f"   [Scene {scene.scene_id}] ({scene.duration_seconds}s)")
            print(f"     Visual: {scene.visual.description[:50]}...")
            print(f"     Audio: {scene.audio.narration[:50]}...")
            
    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_script_generation())
