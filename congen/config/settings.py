
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
    
    # --- Model Lists (Latest & Legacy) ---
    TEXT_MODELS: dict = {
        "Gemini 3.1 Pro (Latest)": "gemini-3.1-pro-preview",
        "Gemini 3.1 Flash (Fast)": "gemini-3.1-flash-preview",
        "Gemini 3.1 Flash-Lite (Cost-efficient)": "gemini-3.1-flash-lite-preview",
        "Gemini 2.5 Pro (Stable)": "gemini-2.5-pro",
        "Gemini 2.5 Flash (Legacy)": "gemini-2.5-flash",
    }
    
    IMAGE_MODELS: dict = {
        "Imagen 4 Ultra (High fidelity)": "imagen-4.0-ultra-generate-001",
        "Imagen 4 (Standard)": "imagen-4.0-generate-001",
        "Nano Banana 2 (Gemini 3.1 Flash Image)": "gemini-3.1-flash-image-preview",
        "Nano Banana Pro (Gemini 3 Pro Image)": "gemini-3-pro-image-preview",
        "Nano Banana (Gemini 2.5 Flash Image)": "gemini-2.5-flash-image",
    }
    
    VIDEO_MODELS: dict = {
        "Veo 3.1 Standard (Highest quality)": "veo-3.1-generate-preview",
        "Veo 3.1 Fast (Low latency)": "veo-3.1-fast-generate-preview",
        "Veo 3.1 Lite (Lowest cost)": "veo-3.1-lite-generate-preview",
    }

    # --- Active Model IDs ---
    MODEL_GEMINI_PRO: str = "gemini-3.1-pro-preview"
    MODEL_IMAGEN: str = "imagen-4.0-ultra-generate-001"
    MODEL_VEO: str = "veo-3.1-generate-preview"
    
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
