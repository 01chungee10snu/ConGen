
import logging
import os
import asyncio
import wave
from pathlib import Path
from typing import Optional

from google import genai
from google.genai import types

from congen.agents.base_agent import BaseAgent
from congen.config.settings import settings

# 로거 설정
logger = logging.getLogger(__name__)


def save_wave_file(filename: Path, pcm: bytes, channels=1, rate=24000, sample_width=2):
    """PCM 데이터를 WAV 파일로 저장"""
    with wave.open(str(filename), "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm)


class AudioGeneratorAgent(BaseAgent):
    """
    텍스트를 음성으로 변환하는 에이전트 (Google Gemini TTS 활용)
    """
    
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            api_key = settings.GOOGLE_API_KEY
        
        if not api_key:
            raise ValueError("GOOGLE_API_KEY is not set")
        
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.5-flash-preview-tts"
        
        logger.info(f"AudioGeneratorAgent initialized with model: {self.model_name}")
        
    async def run(self, text: str, output_path: Path) -> str:
        """
        텍스트를 음성으로 변환하여 WAV 파일로 저장
        
        Args:
            text: 변환할 텍스트
            output_path: 저장할 파일 경로
            
        Returns:
            저장된 파일 경로
        """
        logger.info(f"Generating audio for text: {text[:50]}...")
        
        try:
            # 출력 디렉토리 생성
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Gemini TTS API 호출 (동기 함수를 비동기로 래핑)
            pcm_data = await asyncio.to_thread(
                self._generate_speech,
                text
            )
            
            # WAV로 저장 (공식 문서 방식)
            wav_path = output_path.with_suffix('.wav')
            save_wave_file(wav_path, pcm_data)
            
            logger.info(f"Audio saved to: {wav_path}")
            return str(wav_path)
            
        except Exception as e:
            logger.error(f"Audio generation failed: {e}")
            raise
    
    def _generate_speech(self, text: str) -> bytes:
        """Gemini TTS API 호출"""
        # 한국어 TTS 설정
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name="Kore"  # 한국어 음성
                        )
                    )
                )
            )
        )
        
        # 응답에서 PCM 데이터 추출 (공식 문서 방식)
        data = response.candidates[0].content.parts[0].inline_data.data
        return data


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    logging.basicConfig(level=logging.INFO)
    
    # 테스트
    async def test():
        agent = AudioGeneratorAgent()
        text = "안녕하세요. 오늘은 통계학의 기초입니다."
        output_path = Path("test_google_tts.wav")
        result = await agent.run(text, output_path)
        print(f"Generated: {result}")
    
    asyncio.run(test())
