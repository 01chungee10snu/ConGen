import logging
import os
import asyncio
import wave
from pathlib import Path

from google import genai
from google.genai import types

from congen.agents.base_agent import BaseAgent
from congen.config.settings import settings

# 로거 설정
logger = logging.getLogger(__name__)

class MusicGeneratorAgent(BaseAgent):
    """
    텍스트 프롬프트를 받아 배경음악(BGM)을 생성하는 에이전트 (Lyria-3 활용)
    """
    
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            api_key = settings.GOOGLE_API_KEY
        
        if not api_key:
            raise ValueError("GOOGLE_API_KEY is not set")
        
        self.client = genai.Client(api_key=api_key)
        
    async def run(self, prompt: str, duration_seconds: int, output_path: Path) -> str:
        """
        프롬프트에 맞는 배경음악을 생성하여 WAV 파일로 저장
        """
        model_name = settings.MODEL_MUSIC
        logger.info(f"Generating BGM ({duration_seconds}s) with model: {model_name}")
        
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Lyria API 호출 (동기 함수를 비동기로 래핑)
            # 참고: Lyria API의 정확한 규격은 버전에 따라 다를 수 있으나, 
            # 일반적인 generate_content 오디오 모달리티 패턴을 따릅니다.
            full_prompt = f"Create a high-fidelity, seamless background music track. Style/Mood: {prompt}. Duration: {duration_seconds} seconds. No vocals, instrumental only."
            
            pcm_data = await asyncio.to_thread(
                self._generate_music,
                model_name,
                full_prompt
            )
            
            # WAV로 저장 (Lyria는 고품질 48kHz 지원)
            wav_path = output_path.with_suffix('.wav')
            with wave.open(str(wav_path), "wb") as wf:
                wf.setnchannels(2) # Stereo
                wf.setsampwidth(2) # 16-bit
                wf.setframerate(48000) # 48kHz
                wf.writeframes(pcm_data)
            
            logger.info(f"BGM saved to: {wav_path}")
            return str(wav_path)
            
        except Exception as e:
            logger.error(f"Music generation failed: {e}")
            raise
    
    def _generate_music(self, model_name: str, text: str) -> bytes:
        """Gemini/Lyria API 호출"""
        response = self.client.models.generate_content(
            model=model_name,
            contents=text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
            )
        )
        data = response.candidates[0].content.parts[0].inline_data.data
        return data
