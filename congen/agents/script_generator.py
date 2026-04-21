
import json
import logging
import os
from pathlib import Path
from typing import Optional

from google import genai
from google.genai import types
from google.genai.errors import ClientError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from congen.agents.base_agent import BaseAgent
from congen.config.settings import settings
from congen.models.script import Script

# 로거 설정
logger = logging.getLogger(__name__)

class ScriptGeneratorAgent(BaseAgent):
    """
    자연어 프롬프트를 받아 구조화된 비디오 스크립트(Script 모델)를 생성하는 에이전트
    """
    
    def __init__(self):
        # settings.GOOGLE_API_KEY 대신 os.getenv를 직접 사용하여 Pydantic 파싱 이슈 회피
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            # fallback to settings if env var is missing (though settings loads from env)
            api_key = settings.GOOGLE_API_KEY
            
        if not api_key:
             raise ValueError("GOOGLE_API_KEY is not set")

        self.client = genai.Client(api_key=api_key)
        self.model_name = settings.MODEL_GEMINI_PRO
        self.prompt_template = self._load_prompt_template()
        
    def _load_prompt_template(self) -> str:
        """프롬프트 템플릿 파일 로드"""
        prompt_path = settings.BASE_DIR / "congen" / "config" / "prompts" / "script_generator.txt"
        try:
            return prompt_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            logger.error(f"Prompt template not found at {prompt_path}")
            raise

    @retry(
        retry=retry_if_exception_type(ClientError),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        reraise=True
    )
    def _call_gemini(self, full_prompt: str):
        """Gemini API 호출 (재시도 로직 적용)"""
        # settings에서 최신 모델명을 동적으로 가져옴
        model_name = settings.MODEL_GEMINI_PRO
        logger.info(f"Calling Gemini API with model: {model_name}")
        return self.client.models.generate_content(
            model=model_name,
            contents=full_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.7,
            )
        )

    async def run(self, user_prompt: str) -> Script:
        """
        사용자 프롬프트를 기반으로 스크립트 생성
        """
        logger.info(f"Generating script for prompt: {user_prompt}")
        
        # 프롬프트 구성
        full_prompt = self.prompt_template.format(user_prompt=user_prompt)
        
        try:
            # Gemini API 호출 (재시도 로직 적용)
            response = self._call_gemini(full_prompt)
            
            # 응답 텍스트 추출
            response_text = response.text
            logger.debug(f"Raw API Response: {response_text[:200]}...")
            
            # JSON 파싱
            try:
                data = json.loads(response_text)
                script = Script(**data)
                logger.info(f"Script generated successfully: {script.metadata.title}")
                return script
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Response content: {response_text}")
                raise ValueError("AI generated invalid JSON")
            except Exception as e:
                logger.error(f"Validation failed: {e}")
                raise ValueError(f"Script validation failed: {e}")
                
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            raise

if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv
    load_dotenv()
    
    async def main():
        agent = ScriptGeneratorAgent()
        try:
            script = await agent.run("초등학생을 위한 태양계 행성 소개 영상 (30초)")
            print(f"Title: {script.metadata.title}")
            print(f"Scenes: {len(script.scenes)}")
        except Exception as e:
            print(f"Error: {e}")

    asyncio.run(main())
