
import sys
import os
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가하여 모듈 import 가능하게 함
sys.path.append(str(Path(__file__).resolve().parent.parent))

try:
    from congen.config.settings import settings
    from congen.models.script import Script, Scene, VisualDescription, AudioDescription, ScriptMetadata
    
    print("✅ 모듈 Import 성공")
    
    # 1. 설정 로드 테스트
    print("\n--- Settings Check ---")
    print(f"API Key Loaded: {'Yes' if settings.GOOGLE_API_KEY else 'No'}")
    print(f"Veo Model: {settings.MODEL_VEO}")
    print(f"Output Dir: {settings.OUTPUT_DIR}")
    
    if not settings.GOOGLE_API_KEY.startswith("AIza"):
        print("⚠️ Warning: API Key format looks suspicious (should start with AIza)")
    
    # 2. 데이터 모델 테스트
    print("\n--- Data Model Check ---")
    scene = Scene(
        scene_id=1,
        duration_seconds=5,
        visual=VisualDescription(description="A teacher standing in a classroom"),
        audio=AudioDescription(narration="안녕하세요, 오늘 수업을 시작하겠습니다.")
    )
    
    script = Script(
        metadata=ScriptMetadata(
            title="Test Video",
            topic="Testing",
            target_audience="Developers",
            learning_objective="Check system health",
            total_duration_seconds=60
        ),
        scenes=[scene]
    )
    
    print(f"Script Created: {script.metadata.title}")
    print(f"Scene 1 Narration: {script.scenes[0].audio.narration}")
    print("✅ 데이터 모델 검증 완료")
    
except Exception as e:
    print(f"❌ Setup Check Failed: {e}")
    import traceback
    traceback.print_exc()
