
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

# 프로젝트 루트 디렉토리 (congen 패키지의 상위 디렉토리)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    # --- API Keys ---
    GOOGLE_API_KEY: str
    GOOGLE_CLOUD_PROJECT: Optional[str] = None
    
    # --- Model IDs (검증된 모델 ID 사용) ---
    # 텍스트/스크립트 생성
    MODEL_GEMINI_PRO: str = "gemini-3-pro-preview"
    MODEL_GEMINI_FLASH: str = "gemini-2.0-flash-exp"  # 폴백용
    
    # 이미지 생성
    MODEL_IMAGEN: str = "gemini-3-pro-image-preview" # Nano Banana Pro
    MODEL_IMAGEN_FALLBACK: str = "imagen-4.0-ultra-generate-001"
    
    # 비디오 생성
    MODEL_VEO: str = "veo-3.1-fast-generate-preview"
    MODEL_VEO_FAST: str = "veo-3.1-fast-generate-preview"
    
    # --- Paths ---
    BASE_DIR: Path = BASE_DIR
    OUTPUT_DIR: Path = BASE_DIR / "output"
    TEMP_DIR: Path = BASE_DIR / "temp"
    ASSETS_DIR: Path = BASE_DIR / "assets"
    
    # --- Video Settings ---
    VIDEO_RESOLUTION: str = "1080p"
    VIDEO_ASPECT_RATIO: str = "16:9"
    VIDEO_FPS: int = 24
    
    # --- Cost Control ---
    # Veo 사용 전략: 'full', 'hybrid', 'minimal', 'none'
    VEO_STRATEGY: str = "full" 
    
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"  # .env에 정의되지 않은 변수 무시
    )

    def model_post_init(self, __context):
        """설정 로드 후 후처리"""
        if self.GOOGLE_API_KEY:
            self.GOOGLE_API_KEY = self.GOOGLE_API_KEY.strip()

    def create_dirs(self):
        """필요한 디렉토리 생성"""
        self.OUTPUT_DIR.mkdir(exist_ok=True)
        self.TEMP_DIR.mkdir(exist_ok=True)
        self.ASSETS_DIR.mkdir(exist_ok=True)

# 전역 설정 인스턴스
settings = Settings()

# 초기화 시 디렉토리 생성
settings.create_dirs()
