
import logging
import os
import base64
from pathlib import Path
from typing import Optional

from google import genai
from google.genai import types
from google.genai.errors import ClientError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from congen.agents.base_agent import BaseAgent
from congen.config.settings import settings

# 로거 설정
logger = logging.getLogger(__name__)

class ImageGeneratorAgent(BaseAgent):
    """
    텍스트 프롬프트를 받아 이미지를 생성하는 에이전트
    """
    
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            api_key = settings.GOOGLE_API_KEY
        
        if not api_key:
             raise ValueError("GOOGLE_API_KEY is not set")

        self.client = genai.Client(api_key=api_key)
        self.model_name = settings.MODEL_IMAGEN
        
    # --- Imagen 4 Ultra (Legacy/Fallback) ---
    # @retry(...)
    # def _call_imagen(self, prompt: str):
    #     ...
    
    # --- Nano Banana Pro (Gemini 3 Pro Image) ---
    @retry(
        retry=retry_if_exception_type(ClientError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=30),
        reraise=True
    )
    def _call_nano_banana(self, prompt: str):
        """Nano Banana Pro 호출 (generate_content 사용)"""
        logger.info(f"Calling Nano Banana Pro with model: {self.model_name}")
        
        # 프롬프트 보강 (Global Rule 적용)
        full_prompt = (
            f"Generate a high-quality educational image. "
            f"Style: Consistent, Clean, Modern, Educational Illustration. "
            f"Content: {prompt}. "
            f"Important Rule: If any text appears in the image, it MUST be written in Korean (Hangul)."
        )
        
        return self.client.models.generate_content(
            model=self.model_name,
            contents=full_prompt,
            # config=types.GenerateContentConfig(
            #     # 필요한 경우 설정 추가
            # )
        )

    async def run(self, prompt: str, output_path: Path) -> str:
        """
        이미지 생성 및 저장
        """
        logger.info(f"Generating image for prompt: {prompt[:50]}...")
        
        try:
            # Nano Banana Pro 호출
            response = self._call_nano_banana(prompt)
            
            # 응답에서 이미지 추출
            # Gemini 모델은 텍스트와 이미지를 함께 반환할 수 있음
            # parts를 순회하며 inline_data(이미지)를 찾음
            image_data = None
            
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.inline_data:
                        image_data = part.inline_data.data
                        break
            
            # 만약 inline_data가 없고 executable_code 등이 있다면? (보통 이미지는 inline_data)
            
            if not image_data:
                # 혹시 generate_images처럼 generated_images 속성이 있는지 확인 (SDK 버전에 따라 다름)
                if hasattr(response, 'generated_images') and response.generated_images:
                     image = response.generated_images[0]
                     image.image.save(output_path)
                     logger.info(f"Image saved to: {output_path}")
                     return str(output_path)
                
                logger.error(f"No image data found in response: {response}")
                raise ValueError("No image generated")
            
            # 이미지 저장 (bytes)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # base64 디코딩이 필요할 수도 있고, 이미 bytes일 수도 있음
            # google-genai SDK의 inline_data.data는 보통 bytes임
            with open(output_path, "wb") as f:
                f.write(image_data)
            
            logger.info(f"Image saved to: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            raise

if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv
    load_dotenv()
    
    async def main():
        agent = ImageGeneratorAgent()
        try:
            output = Path("test_nano.png")
            path = await agent.run("A futuristic classroom", output)
            print(f"Generated: {path}")
        except Exception as e:
            print(f"Error: {e}")

    asyncio.run(main())
