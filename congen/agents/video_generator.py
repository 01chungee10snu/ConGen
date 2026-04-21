
import logging
import os
import time
import asyncio
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

class VideoGeneratorAgent(BaseAgent):
    """
    텍스트와 이미지를 받아 비디오를 생성하는 에이전트 (Veo 활용)
    """
    
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            api_key = settings.GOOGLE_API_KEY
        
        if not api_key:
             raise ValueError("GOOGLE_API_KEY is not set")

        self.client = genai.Client(api_key=api_key)
        self.model_name = settings.MODEL_VEO
        
    @retry(
        retry=retry_if_exception_type(ClientError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=10, max=120),
        reraise=True
    )
    def _call_veo(self, prompt: str, image_path: Path):
        """Veo API 호출 (Image-to-Video)"""
        model_name = settings.MODEL_VEO
        logger.info(f"Calling Veo API with model: {model_name}")
        
        # 이미지 파일 읽기
        with open(image_path, "rb") as f:
            image_bytes = f.read()
            
        # Image 객체 생성
        image = types.Image(image_bytes=image_bytes, mime_type="image/png")
        
        # 프롬프트 보강 (Text Preservation 지침 추가)
        full_prompt = (
            f"Cinematic, high quality, 4k. {prompt}. "
            f"CRITICAL INSTRUCTION: Strictly preserve any text, letters, or numbers visible in the input image. "
            f"Do NOT morph, distort, translate, or animate the text. The text must remain perfectly legible and static throughout the video."
        )
        
        # 비디오 생성 요청
        return self.client.models.generate_videos(
            model=model_name,
            prompt=full_prompt,
            image=image, 
            config=types.GenerateVideosConfig(
                aspect_ratio="16:9",
            )
        )

    async def run(self, prompt: str, image_path: Path, output_path: Path) -> str:
        """
        비디오 생성 및 저장
        """
        logger.info(f"Generating video for prompt: {prompt[:50]}...")
        
        try:
            # Veo 호출 (LRO 반환)
            operation = self._call_veo(prompt, image_path)
            
            logger.info(f"Operation object type: {type(operation)}")
            if hasattr(operation, "name"):
                logger.info(f"🎥 Operation Name (ID): {operation.name}")
            
            logger.info("Waiting for video generation to complete (Manual Polling)...")
            
            # 수동 폴링 로직 (공식 문서 기반)
            # https://ai.google.dev/gemini-api/docs/video?hl=ko&example=dialogue
            start_time = time.time()
            timeout_seconds = 600  # 10분 타임아웃
            
            while not operation.done:
                current_time = time.time()
                if current_time - start_time > timeout_seconds:
                    raise TimeoutError(f"Video generation timed out after {timeout_seconds} seconds.")
                
                logger.info("Polling... (Waiting for video generation)")
                await asyncio.sleep(10)
                
                try:
                    # 중요: operation 객체 자체를 전달해야 함
                    # operation.name이 문자열 ID라면 name=operation.name으로 전달해야 할 수도 있음
                    # SDK 버전에 따라 다르지만, 보통 operation 객체나 name 문자열을 받음
                    operation = self.client.operations.get(operation)
                except Exception as e:
                    logger.warning(f"Failed to refresh operation status (retrying): {e}")
                    # 일시적인 네트워크 오류일 수 있으므로 루프 계속 진행
                    continue
            
            logger.info("Operation done.")
            
            # 결과 추출
            response = None
            if hasattr(operation, "response"):
                response = operation.response
            elif hasattr(operation, "result"):
                if callable(operation.result):
                    response = operation.result()
                else:
                    response = operation.result
            
            if response is None:
                 raise ValueError("Video generation completed but no response found.")

            # 응답 처리
            if not hasattr(response, "generated_videos"):
                 logger.error(f"Response does not have generated_videos. Response: {response}")
                 raise ValueError("Invalid response format: missing generated_videos")
                 
            if not response.generated_videos:
                raise ValueError("No videos generated")
                
            video = response.generated_videos[0]
            
            # 비디오 저장
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.info("Downloading video content...")
            try:
                # 공식 문서에 따른 다운로드 절차
                self.client.files.download(file=video.video)
            except Exception as e:
                logger.warning(f"Explicit download failed (might be unnecessary or failed): {e}")

            logger.info(f"Saving video to {output_path}...")
            video.video.save(output_path)
            
            logger.info(f"Video saved to: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Video generation failed: {e}")
            raise

if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv
    from PIL import Image
    
    # 환경 변수 로드
    load_dotenv()
    
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    async def test_video_generation():
        print("🚀 Starting Veo Video Generation Test...")
        
        # 1. 테스트용 이미지 생성 (빨간색 배경)
        test_image_path = Path("temp/test_input.png")
        test_image_path.parent.mkdir(exist_ok=True)
        
        img = Image.new('RGB', (1920, 1080), color='red')
        img.save(test_image_path)
        print(f"✅ Created test image: {test_image_path}")
        
        # 2. 에이전트 초기화
        agent = VideoGeneratorAgent()
        print(f"🔹 Model: {agent.model_name}")
        
        # 3. 비디오 생성 요청
        output_path = Path("temp/test_veo_output.mp4")
        prompt = "A cinematic camera pan over a red surface, high quality, 4k"
        
        try:
            print("⏳ Sending request to Veo API...")
            result = await agent.run(prompt, test_image_path, output_path)
            print(f"🎉 Success! Video saved to: {result}")
        except Exception as e:
            print(f"❌ Error: {e}")

    asyncio.run(test_video_generation())
