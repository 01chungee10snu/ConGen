
import asyncio
import json
import logging
import subprocess
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from PIL import Image, UnidentifiedImageError

from congen.agents.script_generator import ScriptGeneratorAgent
from congen.agents.image_generator import ImageGeneratorAgent
from congen.agents.video_generator import VideoGeneratorAgent
from congen.agents.audio_generator import AudioGeneratorAgent
from congen.agents.music_generator import MusicGeneratorAgent
from congen.models.script import Script
from congen.config.settings import settings

# 로거 설정
logger = logging.getLogger(__name__)


def is_valid_image(file_path: Path) -> bool:
    """이미지 파일 무결성 검증"""
    if not file_path.exists() or file_path.stat().st_size == 0:
        return False
    try:
        with Image.open(file_path) as img:
            img.verify()
        return True
    except (UnidentifiedImageError, IOError):
        return False


async def get_media_duration(file_path: Path) -> float:
    """FFprobe로 미디어 파일 길이(초) 가져오기 (비동기)"""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(file_path)
    ]
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, _ = await process.communicate()
    if process.returncode == 0 and stdout.strip():
        return float(stdout.strip())
    return 0.0


async def is_valid_media(file_path: Path) -> bool:
    """오디오/비디오 파일 무결성 검증 (0바이트 및 재생 가능 여부)"""
    if not file_path.exists() or file_path.stat().st_size == 0:
        return False
    duration = await get_media_duration(file_path)
    return duration > 0.1


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
        
        # 동시성 제어 (Rate Limiting)를 위한 세마포어
        self.image_sem = asyncio.Semaphore(5)
        self.audio_sem = asyncio.Semaphore(5)
        self.video_sem = asyncio.Semaphore(2)  # Veo 모델은 더 엄격하게 제한

        
    def _create_output_dir(self, topic: str) -> Path:
        """타임스탬프 기반 출력 디렉토리 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sanitized_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '_')).strip().replace(' ', '_')
        sanitized_topic = sanitized_topic[:30]
        
        output_dir = settings.OUTPUT_DIR / f"{timestamp}_{sanitized_topic}"
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    async def _generate_images(self, script: Script, output_dir: Path, options: dict = None):
        """이미지 생성 (Nano Banana Pro) - 병렬 처리 (Semaphore 적용)"""
        logger.info("🎨 Step 2: Generating Images (Parallel with Rate Limiting)...")
        images_dir = output_dir / "2_scenes"
        images_dir.mkdir(exist_ok=True)
        options = options or {}
        img_opts = options.get("image", {})
        style = img_opts.get("style", "Modern Educational Illustration")
        color = img_opts.get("color", "Vibrant")
        custom = img_opts.get("custom", "")
        
        async def process_scene(scene):
            image_path = images_dir / f"scene_{scene.scene_id:03d}.png"
            if is_valid_image(image_path):
                scene.image_path = str(image_path)
                return
            elif image_path.exists():
                logger.warning(f"⚠️ Corrupted image found for Scene {scene.scene_id}. Regenerating...")
                image_path.unlink()

            base_prompt = scene.visual.description
            enhanced_prompt = (
                f"{base_prompt}. Style: {style}, Color Palette: {color}. "
                f"High quality, 4k resolution. "
                f"CRITICAL: Maintain realistic physics and strict anatomical correctness. Do not generate morphed or structurally impossible objects. "
            )
            if custom:
                enhanced_prompt += f" Additional instructions: {custom}"

            try:
                # 세마포어로 동시성 제어
                async with self.image_sem:
                    await asyncio.sleep(0.5) # API 딜레이 최소화
                    saved_path = await self.image_agent.run(enhanced_prompt, image_path)
                    scene.image_path = str(saved_path)
            except Exception as e:
                logger.error(f"❌ Failed to generate image for Scene {scene.scene_id}: {e}")

        await asyncio.gather(*(process_scene(scene) for scene in script.scenes))
        
        script_path = output_dir / "1_script.json"
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(script.model_dump(), indent=2, ensure_ascii=False))
        logger.info("✅ Image generation completed.")

    async def _generate_audio(self, script: Script, output_dir: Path, options: dict = None):
        """오디오(TTS) 생성 - 병렬 처리 (Semaphore 적용)"""
        logger.info("🔊 Step 3: Generating Audio (Parallel with Rate Limiting)...")
        audio_dir = output_dir / "3_audio"
        audio_dir.mkdir(exist_ok=True)
        options = options or {}
        
        async def process_scene(scene):
            narration = scene.audio.narration if scene.audio else ""
            if not narration:
                return
            
            audio_path = audio_dir / f"scene_{scene.scene_id:03d}.wav"
            if await is_valid_media(audio_path):
                scene.audio_path = str(audio_path)
                return
            elif audio_path.exists():
                logger.warning(f"⚠️ Corrupted audio found for Scene {scene.scene_id}. Regenerating...")
                audio_path.unlink()

            try:
                async with self.audio_sem:
                    await asyncio.sleep(0.2)
                    saved_path = await self.audio_agent.run(narration, audio_path)
                    scene.audio_path = str(saved_path)
            except Exception as e:
                logger.error(f"❌ Failed to generate audio for Scene {scene.scene_id}: {e}")

        await asyncio.gather(*(process_scene(scene) for scene in script.scenes))
        
        script_path = output_dir / "1_script.json"
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(script.model_dump(), indent=2, ensure_ascii=False))
        logger.info("✅ Audio generation completed.")

    async def _create_static_video(self, image_path: Path, audio_path: Optional[Path], output_path: Path):
        """이미지를 사용하여 줌/팬 효과가 있는 비디오 생성 (비동기 FFmpeg)"""
        # 부모 디렉토리가 삭제되었을 수 있으므로 항상 생성 보장 (QA Fix)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        duration = 5.0
        if audio_path and await is_valid_media(audio_path):
            duration = await get_media_duration(audio_path)
            duration += 0.5
            
        fps = settings.VIDEO_FPS
        total_frames = int(duration * fps)
        zoom_expr = f"min(zoom+0.0005,1.1)"
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
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        _, stderr = await process.communicate()
        
        if process.returncode != 0:
            logger.warning(f"FFmpeg zoompan failed, attempting fallback. Error: {stderr.decode()}")
            cmd_fallback = [
                "ffmpeg", "-y", "-loop", "1", "-i", str(image_path),
                "-c:v", "libx264", "-t", f"{duration:.2f}", "-pix_fmt", "yuv420p",
                "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2", str(output_path)
            ]
            fallback_proc = await asyncio.create_subprocess_exec(
                *cmd_fallback,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await fallback_proc.communicate()
            
        return output_path

    async def _generate_videos(self, script: Script, output_dir: Path, options: dict = None):
        """비디오 생성 (Veo 또는 비동기 FFmpeg) - 병렬 처리 (Semaphore 적용)"""
        logger.info(f"🎥 Step 4: Generating Videos (Strategy: {settings.VEO_STRATEGY})...")
        videos_dir = output_dir / "4_videos"
        videos_dir.mkdir(exist_ok=True)
        options = options or {}
        vid_opts = options.get("video", {})
        camera = vid_opts.get("camera", "Cinematic Pan")
        custom = vid_opts.get("custom", "")
        
        async def process_scene(scene):
            if not scene.image_path or not is_valid_image(Path(scene.image_path)):
                logger.warning(f"⚠️ Valid image not found for Scene {scene.scene_id}, skipping video.")
                return
                
            video_path = videos_dir / f"scene_{scene.scene_id:03d}.mp4"
            if await is_valid_media(video_path):
                scene.video_path = str(video_path)
                return
            elif video_path.exists():
                logger.warning(f"⚠️ Corrupted video found for Scene {scene.scene_id}. Regenerating...")
                video_path.unlink()
            
            audio_path = Path(output_dir / "3_audio" / f"scene_{scene.scene_id:03d}.wav")
            if not await is_valid_media(audio_path):
                audio_path = None
            
            try:
                use_veo = False
                if settings.VEO_STRATEGY == "full":
                    use_veo = True
                elif settings.VEO_STRATEGY == "hybrid":
                    if scene.scene_id == 1 or scene.scene_id % 3 == 0:
                        use_veo = True
                
                if use_veo:
                    enhanced_prompt = (
                        f"{scene.visual.description}. Camera Motion: {camera}. "
                        f"CRITICAL: Ensure perfect temporal consistency, zero inter-frame flicker, and highly stable lighting. "
                        f"Subjects must not drift, morph, or deform over time. Maintain rigid anatomical and physical structure."
                    )
                    if custom:
                        enhanced_prompt += f" Extra instructions: {custom}"

                    logger.info(f"   Generating AI video (Veo) for Scene {scene.scene_id}")
                    # 세마포어로 동시성 제어 (Veo는 엄격하게 제한)
                    async with self.video_sem:
                        saved_path = await self.video_agent.run(
                            prompt=enhanced_prompt,
                            image_path=Path(scene.image_path),
                            output_path=video_path
                        )
                else:
                    logger.info(f"   Creating static video for Scene {scene.scene_id}")
                    saved_path = await self._create_static_video(
                        Path(scene.image_path), 
                        audio_path, 
                        video_path
                    )
                scene.video_path = str(saved_path)
                
            except Exception as e:
                logger.error(f"❌ Failed to generate video for Scene {scene.scene_id}: {e}")
                try:
                    await self._create_static_video(Path(scene.image_path), audio_path, video_path)
                    scene.video_path = str(video_path)
                except Exception as fb_err:
                    pass
        
        await asyncio.gather(*(process_scene(scene) for scene in script.scenes))
        
        script_path = output_dir / "1_script.json"
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(script.model_dump(), indent=2, ensure_ascii=False))
        logger.info("✅ Video generation completed.")

    async def _assemble_final_video(self, script: Script, output_dir: Path, options: dict = None):
        """최종 영상 비동기 조립 및 자원 정리"""
        logger.info("🎬 Step 5: Assembling Final Video (Async FFmpeg)...")
        options = options or {}
        music_opts = options.get("music", {})
        m_genre = music_opts.get("genre", "Instrumental")
        m_mood = music_opts.get("mood", "Engaging")
        m_custom = music_opts.get("custom", "")
        
        video_dir = output_dir / "4_videos"
        audio_dir = output_dir / "3_audio"
        temp_dir = output_dir / "temp"
        temp_dir.mkdir(exist_ok=True)
        
        available_scenes = []
        for scene in script.scenes:
            video_path = video_dir / f"scene_{scene.scene_id:03d}.mp4"
            audio_path = audio_dir / f"scene_{scene.scene_id:03d}.wav"
            if video_path.exists() and audio_path.exists():
                audio_duration = await get_media_duration(audio_path)
                available_scenes.append({
                    "scene_id": scene.scene_id,
                    "video": video_path,
                    "audio": audio_path,
                    "audio_duration": audio_duration
                })
        
        if not available_scenes:
            logger.warning("⚠️ 조립할 수 있는 완전한 씬이 없습니다.")
            return
        
        # 씬 병합 (비동기) + Audio Fade 처리 (Harsh Cuts 방지)
        merged_files = []
        for scene_data in available_scenes:
            scene_id = scene_data["scene_id"]
            merged_path = temp_dir / f"merged_{scene_id:03d}.mp4"
            if merged_path.exists():
                merged_files.append(merged_path)
                continue

            duration = scene_data['audio_duration']
            fade_out_start = duration - 0.2 if duration > 0.4 else duration

            # Audio fade in/out 필터 적용 (틱 노이즈 방지 및 부드러운 연결)
            audio_filter = f"afade=t=in:ss=0:d=0.1,afade=t=out:st={fade_out_start}:d=0.2"

            cmd = [
                "ffmpeg", "-y", "-stream_loop", "-1",
                "-i", str(scene_data["video"]), "-i", str(scene_data["audio"]),
                "-filter_complex", f"[1:a]{audio_filter}[a]",
                "-map", "0:v:0", "-map", "[a]",
                "-c:v", "libx264", 
                "-pix_fmt", "yuv420p",                # 픽셀 포맷 강제 통일 (8비트)
                "-r", str(settings.VIDEO_FPS),        # 프레임 레이트 고정 강제
                "-video_track_timescale", "90000",    # Timebase 정규화
                "-c:a", "aac", "-ar", "48000", "-ac", "2", # 오디오 샘플레이트/채널 정규화
                "-t", f"{duration:.2f}", "-shortest", str(merged_path)
            ]
            proc = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()
            if proc.returncode == 0:
                merged_files.append(merged_path)
        
        if not merged_files:
            return
        
        concat_list_path = temp_dir / "concat_list.txt"
        with open(concat_list_path, "w", encoding="utf-8") as f:
            for merged_file in merged_files:
                f.write(f"file '{merged_file.name}'\n")

        
        # 1차 조립 (비동기)
        raw_output = temp_dir / "raw_video.mp4"
        cmd_concat = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(concat_list_path), "-c", "copy", str(raw_output)
        ]
        proc_concat = await asyncio.create_subprocess_exec(
            *cmd_concat, cwd=str(temp_dir), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        _, stderr_concat = await proc_concat.communicate()
        
        if proc_concat.returncode != 0:
            logger.error(f"❌ Concat failed: {stderr_concat.decode()}")
            return
            
        total_duration = await get_media_duration(raw_output)
        final_output = output_dir / "final_video.mp4"
        
        bgm_prompt = f"Genre: {m_genre}, Mood: {m_mood}."
        if m_custom:
            bgm_prompt += f" Details: {m_custom}"
        bgm_prompt += " Background music for an educational video, neutral tone, instrumental."
        bgm_path = temp_dir / "bgm.wav"
        
        try:
            logger.info("🎵 Generating BGM (Lyria)...")
            await self.music_agent.run(bgm_prompt, int(total_duration) + 1, bgm_path)
            
            logger.info("🎛️ Mixing BGM with video (Async)...")
            cmd_mix = [
                "ffmpeg", "-y", "-i", str(raw_output), "-i", str(bgm_path),
                "-filter_complex", "[0:a]volume=1.0[a0];[1:a]volume=0.3[a1];[a0][a1]amix=inputs=2:duration=first:dropout_transition=2[a]",
                "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", str(final_output)
            ]
            proc_mix = await asyncio.create_subprocess_exec(
                *cmd_mix, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            await proc_mix.communicate()
            if proc_mix.returncode != 0:
                import shutil
                shutil.copy(raw_output, final_output)
        except Exception as e:
            logger.error(f"⚠️ BGM Generation skipped/failed: {e}")
            import shutil
            shutil.copy(raw_output, final_output)
        
        # --- Garbage Collection (임시 파일 청소) ---
        logger.info("🧹 Cleaning up temporary files...")
        try:
            import shutil
            shutil.rmtree(temp_dir)
            logger.info(f"   Deleted temp directory: {temp_dir}")
        except Exception as e:
            logger.warning(f"   Failed to clean temp directory: {e}")
        
        duration = await get_media_duration(final_output)
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
