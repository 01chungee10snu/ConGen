
import asyncio
import json
import logging
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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

def run_ffmpeg(cmd: list, cwd: str = None) -> bool:
    """FFmpeg 명령 실행"""
    logger.info(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            return False
        return True
    except Exception as e:
        logger.error(f"FFmpeg execution failed: {e}")
        return False

async def main():
    load_dotenv()
    
    print("\n" + "="*60)
    print("🎬 ConGen: Final Video Assembly (FFmpeg)")
    print("="*60)
    
    # 가장 최근 결과 폴더 찾기
    output_root = Path(__file__).resolve().parent / "output"
    dirs = sorted([d for d in output_root.iterdir() if d.is_dir()], key=lambda x: x.stat().st_mtime, reverse=True)
    
    if not dirs:
        print("❌ No result folders found.")
        return
    
    latest_dir = dirs[0]
    print(f"📂 Target Directory: {latest_dir}")
    
    video_dir = latest_dir / "4_videos"
    audio_dir = latest_dir / "3_audio"
    temp_dir = latest_dir / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    # 사용 가능한 씬 확인 (비디오와 오디오 모두 있는 씬)
    available_scenes = []
    for i in range(1, 6):
        video_path = video_dir / f"scene_{i:03d}.mp4"
        audio_path = audio_dir / f"scene_{i:03d}.wav"
        
        if video_path.exists() and audio_path.exists():
            audio_duration = get_media_duration(audio_path)
            video_duration = get_media_duration(video_path)
            
            available_scenes.append({
                "scene_id": i,
                "video": video_path,
                "audio": audio_path,
                "audio_duration": audio_duration,
                "video_duration": video_duration
            })
            print(f"✅ Scene {i}: Video ({video_duration:.1f}s) + Audio ({audio_duration:.1f}s)")
        else:
            missing = []
            if not video_path.exists():
                missing.append("video")
            if not audio_path.exists():
                missing.append("audio")
            print(f"⚠️ Scene {i}: Missing {', '.join(missing)}")
    
    if not available_scenes:
        print("❌ No complete scenes available for assembly.")
        return
    
    print(f"\n📝 Assembling {len(available_scenes)} scenes...")
    
    # Step 1: 각 씬의 비디오를 오디오 길이에 맞춰 조정 후 합치기
    merged_files = []
    for scene in available_scenes:
        scene_id = scene["scene_id"]
        video_path = scene["video"]
        audio_path = scene["audio"]
        audio_duration = scene["audio_duration"]
        video_duration = scene["video_duration"]
        merged_path = temp_dir / f"merged_{scene_id:03d}.mp4"
        
        print(f"\n🔧 Scene {scene_id}: Merging video + audio...")
        print(f"   Audio duration: {audio_duration:.1f}s, Video duration: {video_duration:.1f}s")
        
        # 비디오를 오디오 길이에 맞춰 반복(loop) - stream_loop 사용
        # 오디오 길이만큼 비디오를 반복하고, 오디오 끝나면 종료
        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1",  # 무한 반복
            "-i", str(video_path),
            "-i", str(audio_path),
            "-c:v", "libx264",
            "-c:a", "aac",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-t", str(audio_duration),  # 오디오 길이만큼 자르기
            "-shortest",
            str(merged_path)
        ]
        
        if run_ffmpeg(cmd):
            merged_files.append(merged_path)
            result_duration = get_media_duration(merged_path)
            print(f"   ✅ Created: {merged_path.name} ({result_duration:.1f}s)")
        else:
            print(f"   ❌ Failed to merge scene {scene_id}")
    
    if not merged_files:
        print("❌ No merged files created.")
        return
    
    # Step 2: 모든 씬을 하나로 연결 (concat)
    print(f"\n🔗 Concatenating {len(merged_files)} clips...")
    
    # concat 리스트 파일 생성
    concat_list_path = temp_dir / "concat_list.txt"
    with open(concat_list_path, "w", encoding="utf-8") as f:
        for merged_file in merged_files:
            f.write(f"file '{merged_file.name}'\n")
    
    # 최종 출력 파일
    final_output = latest_dir / "final_video.mp4"
    
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_list_path),
        "-c", "copy",
        str(final_output)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(temp_dir))
    
    if result.returncode == 0:
        final_duration = get_media_duration(final_output)
        print(f"\n🎉 Final video created: {final_output}")
        print(f"   Duration: {final_duration:.1f}s")
        print(f"   Size: {final_output.stat().st_size / 1024 / 1024:.2f} MB")
    else:
        print(f"❌ Concat failed: {result.stderr}")

if __name__ == "__main__":
    asyncio.run(main())
