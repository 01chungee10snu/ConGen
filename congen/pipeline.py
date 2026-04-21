
import asyncio
import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from congen.agents.script_generator import ScriptGeneratorAgent
from congen.agents.image_generator import ImageGeneratorAgent
from congen.agents.video_generator import VideoGeneratorAgent
from congen.agents.audio_generator import AudioGeneratorAgent
from congen.agents.music_generator import MusicGeneratorAgent
from congen.models.script import Script
from congen.config.settings import settings

# 로거 설정
logger = logging.getLogger(__name__)


def get_media_duration(file_path: Path) -> float:
    """FFprobe로 미디어 파일 길이(초) 가져오기"""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(file_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0 and result.stdout.strip():
        return float(result.stdout.strip())
    return 0.0


class VideoGenerationPipeline:
    """
    교육 영상 제작을 위한 전체 파이프라인 관리자
    """
    
    def __init__(self):
        self.script_agent = ScriptGeneratorAgent()
        self.image_agent = ImageGeneratorAgent()
        self.video_agent = VideoGeneratorAgent()
        self.audio_agent = AudioGeneratorAgent()
        self.music_agent = MusicGeneratorAgent()
        
    def _create_output_dir(self, topic: str) -> Path:
        """타임스탬프 기반 출력 디렉토리 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sanitized_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '_')).strip().replace(' ', '_')
        sanitized_topic = sanitized_topic[:30]
        
        output_dir = settings.OUTPUT_DIR / f"{timestamp}_{sanitized_topic}"
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    async def _generate_images(self, script: Script, output_dir: Path):
        """이미지 생성 (Nano Banana Pro) - 병렬 처리"""
        logger.info("🎨 Step 2: Generating Images (Parallel)...")
        images_dir = output_dir / "2_scenes"
        images_dir.mkdir(exist_ok=True)
        
        async def process_scene(scene):
            image_path = images_dir / f"scene_{scene.scene_id:03d}.png"
            
            # 이미 존재하면 스킵
            if image_path.exists():
                logger.info(f"   Image already exists for Scene {scene.scene_id}, skipping.")
                scene.image_path = str(image_path)
                return

            logger.info(f"   Generating image for Scene {scene.scene_id}...")
            enhanced_prompt = f"Educational illustration, high quality, 4k, {scene.visual.description}"
            
            try:
                # API 부하 분산을 위해 약간의 딜레이 (선택 사항)
                await asyncio.sleep(scene.scene_id * 0.5)
                saved_path = await self.image_agent.run(enhanced_prompt, image_path)
                scene.image_path = str(saved_path)
            except Exception as e:
                logger.error(f"❌ Failed to generate image for Scene {scene.scene_id}: {e}")

        # 모든 씬에 대해 병렬 실행
        await asyncio.gather(*(process_scene(scene) for scene in script.scenes))
        
        # 스크립트 업데이트
        script_path = output_dir / "1_script.json"
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(script.model_dump(), indent=2, ensure_ascii=False))
        logger.info("✅ Image generation completed.")

    async def _generate_audio(self, script: Script, output_dir: Path):
        """오디오(TTS) 생성 - 병렬 처리"""
        logger.info("🔊 Step 3: Generating Audio (Parallel)...")
        audio_dir = output_dir / "3_audio"
        audio_dir.mkdir(exist_ok=True)
        
        async def process_scene(scene):
            narration = scene.audio.narration if scene.audio else ""
            if not narration:
                return
            
            audio_path = audio_dir / f"scene_{scene.scene_id:03d}.wav"
            
            # 이미 존재하면 스킵
            if audio_path.exists():
                logger.info(f"   Audio already exists for Scene {scene.scene_id}, skipping.")
                scene.audio_path = str(audio_path)
                return

            try:
                # API 부하 분산을 위해 약간의 딜레이
                await asyncio.sleep(scene.scene_id * 0.2)
                saved_path = await self.audio_agent.run(narration, audio_path)
                scene.audio_path = str(saved_path)
                logger.info(f"   ✅ Audio saved: {audio_path.name}")
            except Exception as e:
                logger.error(f"❌ Failed to generate audio for Scene {scene.scene_id}: {e}")

        await asyncio.gather(*(process_scene(scene) for scene in script.scenes))
        
        # 스크립트 업데이트
        script_path = output_dir / "1_script.json"
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(script.model_dump(), indent=2, ensure_ascii=False))
        logger.info("✅ Audio generation completed.")

    def _create_static_video(self, image_path: Path, audio_path: Optional[Path], output_path: Path):
        """이미지를 사용하여 줌/팬 효과가 있는 비디오 생성 (Ken Burns effect)"""
        duration = 5.0
        if audio_path and audio_path.exists():
            duration = get_media_duration(audio_path)
            duration += 0.5
            
        # Ken Burns 효과: 1.1배 줌인하면서 중심 이동
        # scale=8000:-1 는 고품질 줌을 위해 내부 해상도 확대
        # zoompan filter: z=줌레벨, x,y=중심좌표, d=지속프레임(duration * fps)
        fps = settings.VIDEO_FPS
        total_frames = int(duration * fps)
        
        # 줌 효과: 1.0에서 1.1로 서서히 확대
        zoom_expr = f"min(zoom+0.0005,1.1)"
        # 중심 이동: 약간의 패닝 효과
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = "ih/2-(ih/zoom/2)"
        
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(image_path),
            "-vf", f"zoompan=z='{zoom_expr}':x='{x_expr}':y='{y_expr}':d={total_frames}:s=1920x1080,fps={fps}",
            "-c:v", "libx264",
            "-t", f"{duration:.2f}",
            "-pix_fmt", "yuv420p",
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"FFmpeg zoompan failed: {result.stderr}")
            # 폴백: 줌팬 없이 단순 생성
            cmd_fallback = [
                "ffmpeg", "-y",
                "-loop", "1",
                "-i", str(image_path),
                "-c:v", "libx264",
                "-t", f"{duration:.2f}",
                "-pix_fmt", "yuv420p",
                "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
                str(output_path)
            ]
            subprocess.run(cmd_fallback)
            
        return output_path

    async def _generate_videos(self, script: Script, output_dir: Path):
        """비디오 생성 (Veo 또는 FFmpeg) - 병렬 처리 및 하이브리드 전략"""
        logger.info(f"🎥 Step 4: Generating Videos (Strategy: {settings.VEO_STRATEGY})...")
        videos_dir = output_dir / "4_videos"
        videos_dir.mkdir(exist_ok=True)
        
        async def process_scene(scene):
            if not scene.image_path or not Path(scene.image_path).exists():
                return
                
            video_path = videos_dir / f"scene_{scene.scene_id:03d}.mp4"
            
            if video_path.exists():
                logger.info(f"   Video already exists for Scene {scene.scene_id}, skipping.")
                scene.video_path = str(video_path)
                return
            
            audio_path = Path(output_dir / "3_audio" / f"scene_{scene.scene_id:03d}.wav")
            if not audio_path.exists():
                audio_path = None
            
            try:
                # 전략에 따른 결정
                use_veo = False
                if settings.VEO_STRATEGY == "full":
                    use_veo = True
                elif settings.VEO_STRATEGY == "hybrid":
                    # 하이브리드: 1번 씬과 매 3번째 씬마다 Veo 사용
                    if scene.scene_id == 1 or scene.scene_id % 3 == 0:
                        use_veo = True
                
                if use_veo:
                    logger.info(f"   Generating AI video (Veo) for Scene {scene.scene_id}")
                    # Veo는 API 레이트 리밋과 실행 시간이 길어 씬별로 약간의 순차적 지연을 줌
                    await asyncio.sleep(scene.scene_id * 5) 
                    saved_path = await self.video_agent.run(
                        prompt=scene.visual.description,
                        image_path=Path(scene.image_path),
                        output_path=video_path
                    )
                else:
                    logger.info(f"   Creating static video for Scene {scene.scene_id}")
                    saved_path = await asyncio.to_thread(
                        self._create_static_video, 
                        Path(scene.image_path), 
                        audio_path, 
                        video_path
                    )

                scene.video_path = str(saved_path)
                
            except Exception as e:
                logger.error(f"❌ Failed to generate video for Scene {scene.scene_id}: {e}")
                # 실패 시 폴백
                try:
                    logger.info(f"   Attempting fallback to static video for Scene {scene.scene_id}")
                    self._create_static_video(Path(scene.image_path), audio_path, video_path)
                    scene.video_path = str(video_path)
                except Exception as fb_err:
                    logger.error(f"   ❌ Fallback failed: {fb_err}")
        
        # 비디오 생성은 리소스 소모가 크므로 세마포어로 동시 실행 개수 제한 (옵션)
        # 여기서는 일단 모두 gather로 실행 (Veo 내부에서 폴링하므로 gather도 가능)
        await asyncio.gather(*(process_scene(scene) for scene in script.scenes))
        
        # 스크립트 업데이트
        script_path = output_dir / "1_script.json"
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(script.model_dump(), indent=2, ensure_ascii=False))
        logger.info("✅ Video generation completed.")

    async def _assemble_final_video(self, script: Script, output_dir: Path):
        """최종 영상 조립 (FFmpeg)"""
        logger.info("🎬 Step 5: Assembling Final Video (FFmpeg)...")
        
        video_dir = output_dir / "4_videos"
        audio_dir = output_dir / "3_audio"
        temp_dir = output_dir / "temp"
        temp_dir.mkdir(exist_ok=True)
        
        # 사용 가능한 씬 확인
        available_scenes = []
        for scene in script.scenes:
            video_path = video_dir / f"scene_{scene.scene_id:03d}.mp4"
            audio_path = audio_dir / f"scene_{scene.scene_id:03d}.wav"
            
            if video_path.exists() and audio_path.exists():
                audio_duration = get_media_duration(audio_path)
                available_scenes.append({
                    "scene_id": scene.scene_id,
                    "video": video_path,
                    "audio": audio_path,
                    "audio_duration": audio_duration
                })
        
        if not available_scenes:
            logger.warning("⚠️ No complete scenes for assembly.")
            return
        
        # 각 씬 합치기
        merged_files = []
        for scene_data in available_scenes:
            scene_id = scene_data["scene_id"]
            merged_path = temp_dir / f"merged_{scene_id:03d}.mp4"
            
            if merged_path.exists():
                merged_files.append(merged_path)
                continue

            cmd = [
                "ffmpeg", "-y",
                "-stream_loop", "-1",
                "-i", str(scene_data["video"]),
                "-i", str(scene_data["audio"]),
                "-c:v", "libx264",
                "-c:a", "aac",
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-t", f"{scene_data['audio_duration']:.2f}",
                "-shortest",
                str(merged_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                merged_files.append(merged_path)
                logger.info(f"   ✅ Merged scene {scene_id}")
            else:
                logger.error(f"   ❌ Failed to merge scene {scene_id}: {result.stderr}")
        
        if not merged_files:
            logger.error("❌ No merged files created.")
            return
        
        # concat 리스트 생성
        concat_list_path = temp_dir / "concat_list.txt"
        with open(concat_list_path, "w", encoding="utf-8") as f:
            for merged_file in merged_files:
                f.write(f"file '{merged_file.name}'\n")
        
        # 1차 조립 (영상 + TTS)
        raw_output = temp_dir / "raw_video.mp4"
        cmd_concat = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list_path),
            "-c", "copy",
            str(raw_output)
        ]
        
        result_concat = subprocess.run(cmd_concat, capture_output=True, text=True, cwd=str(temp_dir))
        if result_concat.returncode != 0:
            logger.error(f"❌ Concat failed: {result_concat.stderr}")
            return
            
        total_duration = get_media_duration(raw_output)
        
        # BGM 생성 및 믹싱 (옵션)
        final_output = output_dir / "final_video.mp4"
        bgm_prompt = "Soft, engaging, instrumental background music for an educational video, neutral tone"
        bgm_path = temp_dir / "bgm.wav"
        
        try:
            logger.info("🎵 Generating BGM (Lyria)...")
            await self.music_agent.run(bgm_prompt, int(total_duration) + 1, bgm_path)
            
            # 오디오 믹싱 (TTS 볼륨 유지, BGM 볼륨 감소)
            logger.info("🎛️ Mixing BGM with video...")
            cmd_mix = [
                "ffmpeg", "-y",
                "-i", str(raw_output),
                "-i", str(bgm_path),
                "-filter_complex", "[0:a]volume=1.0[a0];[1:a]volume=0.3[a1];[a0][a1]amix=inputs=2:duration=first:dropout_transition=2[a]",
                "-map", "0:v",
                "-map", "[a]",
                "-c:v", "copy",
                "-c:a", "aac",
                str(final_output)
            ]
            result_mix = subprocess.run(cmd_mix, capture_output=True, text=True)
            if result_mix.returncode != 0:
                logger.error(f"❌ Audio mix failed: {result_mix.stderr}")
                # 믹싱 실패 시 원본 복사
                import shutil
                shutil.copy(raw_output, final_output)
        except Exception as e:
            logger.error(f"⚠️ BGM Generation skipped/failed: {e}")
            import shutil
            shutil.copy(raw_output, final_output)
        
        duration = get_media_duration(final_output)
        size_mb = final_output.stat().st_size / 1024 / 1024
        logger.info(f"✅ Final video created: {final_output}")
        logger.info(f"   Duration: {duration:.1f}s, Size: {size_mb:.2f} MB")

    async def run(self, topic: str, output_dir: Optional[Path] = None) -> Path:
        """
        전체 파이프라인 실행 (신규 생성 또는 기존 재개 통합)
        """
        if output_dir:
            logger.info(f"🚀 Resuming pipeline from: {output_dir}")
            script_path = output_dir / "1_script.json"
            if not script_path.exists():
                 raise FileNotFoundError(f"Script not found in {output_dir}")
            with open(script_path, "r", encoding="utf-8") as f:
                script = Script(**json.load(f))
        else:
            logger.info(f"🚀 Starting new pipeline for topic: {topic}")
            output_dir = self._create_output_dir(topic)
            logger.info(f"📂 Output directory: {output_dir}")
            
            # 1. 스크립트 생성
            logger.info("📝 Step 1: Generating Script...")
            script = await self.script_agent.run(topic)
            script_path = output_dir / "1_script.json"
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(script.model_dump(), indent=2, ensure_ascii=False))
            logger.info(f"✅ Script saved to: {script_path}")

        # 2. 이미지 생성
        await self._generate_images(script, output_dir)
        
        # 3. 오디오 생성
        await self._generate_audio(script, output_dir)
        
        # 4. 비디오 생성
        await self._generate_videos(script, output_dir)
        
        # 5. 최종 조립
        await self._assemble_final_video(script, output_dir)
        
        logger.info(f"🎉 Pipeline finished successfully! Results in: {output_dir}")
        return output_dir

    async def run_from_existing(self, output_dir: Path):
        """하위 호환성을 위해 유지"""
        return await self.run("", output_dir=output_dir)



if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    
    async def main():
        pipeline = VideoGenerationPipeline()
        await pipeline.run("통계 기초: 평균, 분산, 표준편차")
        
    asyncio.run(main())
