
from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class VisualDescription(BaseModel):
    """장면의 시각적 요소 묘사"""
    description: str = Field(..., description="장면의 상세한 시각적 묘사 (이미지 생성 프롬프트용)")
    camera_angle: Optional[str] = Field(None, description="카메라 앵글 (예: Close-up, Wide shot)")
    movement: Optional[str] = Field(None, description="카메라 움직임 (예: Pan right, Zoom in)")
    text_overlay: Optional[str] = Field(None, description="화면에 표시될 텍스트 (자막 아님)")

class AudioDescription(BaseModel):
    """장면의 오디오 요소 묘사"""
    narration: str = Field(..., description="내레이션 대사")
    sound_effects: Optional[str] = Field(None, description="배경음 또는 효과음 설명")
    emotion: Optional[str] = Field("neutral", description="내레이션 감정 톤")

class Scene(BaseModel):
    """개별 장면 정의"""
    scene_id: int = Field(..., description="장면 번호 (1부터 시작)")
    duration_seconds: int = Field(..., description="예상 지속 시간 (초)")
    visual: VisualDescription
    audio: AudioDescription
    transition: Optional[str] = Field(None, description="다음 장면으로의 전환 효과")
    
    # 생성된 자산 경로 (초기엔 None)
    image_path: Optional[str] = None
    video_path: Optional[str] = None
    audio_path: Optional[str] = None

class ScriptMetadata(BaseModel):
    """스크립트 메타데이터"""
    title: str
    topic: str
    target_audience: str
    learning_objective: str
    total_duration_seconds: int
    style: str = "educational"
    language: str = "ko"

class Script(BaseModel):
    """전체 비디오 스크립트"""
    metadata: ScriptMetadata
    scenes: List[Scene]
