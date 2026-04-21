
import streamlit as st
import asyncio
import json
import os
import shutil
from pathlib import Path
from dotenv import load_dotenv
import logging

from congen.pipeline import VideoGenerationPipeline
from congen.config.settings import settings
from congen.models.script import Script

# 페이지 설정
st.set_page_config(
    page_title="ConGen Pro - 단계별 AI 영상 제작",
    page_icon="🎬",
    layout="wide"
)

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- 세션 상태 관리 ---
if "pipeline" not in st.session_state:
    st.session_state.pipeline = VideoGenerationPipeline()
if "step" not in st.session_state:
    st.session_state.step = 1  # 1: Script, 2: Audio, 3: Image, 4: Video, 5: Final
if "script" not in st.session_state:
    st.session_state.script = None
if "output_dir" not in st.session_state:
    st.session_state.output_dir = None
if "selected_assets" not in st.session_state:
    st.session_state.selected_assets = {} # {scene_id: {"audio": path, "image": path, "video": path}}

def reset_all():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# --- 사이드바 ---
with st.sidebar:
    st.title("🎬 ConGen Pro")
    st.info("비용과 품질의 균형을 위해 단계별로 결과물을 확정하며 진행하세요.")
    
    # 진행도 표시
    steps = ["📝 스크립트", "🔊 음성 확정", "🎨 이미지 선택", "🎥 비디오 생성", "🎬 최종 조립"]
    current_step = st.session_state.step
    for i, step_name in enumerate(steps):
        status = "🔵" if i + 1 == current_step else ("✅" if i + 1 < current_step else "⚪")
        st.write(f"{status} {step_name}")
    
    st.divider()
    if st.button("프로젝트 초기화", type="secondary"):
        reset_all()

# --- 메인 영역 ---
st.title("🚀 AI 교육 영상 제작 파이프라인")

# --- Step 1: 스크립트 생성 및 편집 ---
if st.session_state.step == 1:
    st.header("Step 1: 📝 교육 스크립트 설계")
    topic = st.text_area("영상 주제 및 핵심 내용을 입력하세요", placeholder="예: 중학생을 위한 함수 개념 설명 (3개 장면, 1분 내외)", height=150)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("스크립트 생성하기", type="primary", use_container_width=True):
            with st.spinner("AI가 스크립트를 작성 중입니다..."):
                output_dir = st.session_state.pipeline._create_output_dir(topic)
                script = asyncio.run(st.session_state.pipeline.script_agent.run(topic))
                st.session_state.script = script
                st.session_state.output_dir = output_dir
                st.rerun()
                
    if st.session_state.script:
        st.divider()
        st.subheader("🖋️ 스크립트 상세 편집")
        with st.expander("프로젝트 메타데이터 수정"):
            st.session_state.script.metadata.title = st.text_input("영상 제목", st.session_state.script.metadata.title)
            st.session_state.script.metadata.learning_objective = st.text_input("학습 목표", st.session_state.script.metadata.learning_objective)

        for i, scene in enumerate(st.session_state.script.scenes):
            with st.container(border=True):
                st.markdown(f"### 🎬 Scene {scene.scene_id}")
                c1, c2 = st.columns([2, 3])
                with c1:
                    scene.visual.description = st.text_area("비주얼 묘사 (이미지 프롬프트)", scene.visual.description, key=f"v_{i}", height=120)
                with c2:
                    scene.audio.narration = st.text_area("내레이션 (음성 대사)", scene.audio.narration, key=f"a_{i}", height=120)
        
        if st.button("스크립트 확정 및 음성 생성 단계로 이동 ➡️", type="primary"):
            # 스크립트 저장
            script_path = st.session_state.output_dir / "1_script.json"
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(st.session_state.script.model_dump(), indent=2, ensure_ascii=False))
            st.session_state.step = 2
            st.rerun()

# --- Step 2: 음성 생성 및 검토 ---
elif st.session_state.step == 2:
    st.header("Step 2: 🔊 음성(TTS) 생성 및 선택")
    st.info("각 장면의 내레이션 음성을 생성합니다. 대사가 길 경우 내용을 수정하고 다시 생성할 수 있습니다.")
    
    all_audio_done = True
    for scene in st.session_state.script.scenes:
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**Scene {scene.scene_id} 대사:**")
                st.write(scene.audio.narration)
            
            audio_path = st.session_state.output_dir / "3_audio" / f"scene_{scene.scene_id:03d}.wav"
            
            with col2:
                if st.button(f"음성 생성/재생성 ({scene.scene_id})", key=f"btn_a_{scene.scene_id}"):
                    with st.spinner("생성 중..."):
                        asyncio.run(st.session_state.pipeline.audio_agent.run(scene.audio.narration, audio_path))
                
                if audio_path.exists():
                    st.audio(str(audio_path))
                    st.session_state.selected_assets.setdefault(scene.scene_id, {})["audio"] = str(audio_path)
                    scene.audio_path = str(audio_path)
                else:
                    all_audio_done = False
                    st.warning("음성이 필요합니다.")

    if st.button("⬅️ 이전 단계 (스크립트 수정)"):
        st.session_state.step = 1
        st.rerun()
    
    if all_audio_done:
        if st.button("모든 음성 확정 및 이미지 생성 단계로 이동 ➡️", type="primary"):
            st.session_state.step = 3
            st.rerun()

# --- Step 3: 이미지 생성 및 선택 (Variations) ---
elif st.session_state.step == 3:
    st.header("Step 3: 🎨 장면 이미지 생성 및 선택")
    st.info("장면마다 여러 장을 생성해보고 가장 적절한 이미지를 선택하세요.")
    
    all_images_selected = True
    for scene in st.session_state.script.scenes:
        with st.container(border=True):
            st.markdown(f"### Scene {scene.scene_id}")
            st.write(f"**이미지 프롬프트:** {scene.visual.description}")
            
            img_dir = st.session_state.output_dir / "2_scenes" / f"scene_{scene.scene_id:03d}"
            img_dir.mkdir(parents=True, exist_ok=True)
            
            # 현재 선택된 이미지 표시
            selected_img = st.session_state.selected_assets.get(scene.scene_id, {}).get("image")
            
            # 이미지 생성 버튼
            if st.button(f"새로운 이미지 옵션 생성 ({scene.scene_id})", key=f"gen_img_{scene.scene_id}"):
                with st.spinner("이미지 생성 중..."):
                    idx = len(list(img_dir.glob("*.png"))) + 1
                    new_img_path = img_dir / f"variant_{idx:02d}.png"
                    enhanced_prompt = f"Educational illustration, high quality, 4k, {scene.visual.description}"
                    asyncio.run(st.session_state.pipeline.image_agent.run(enhanced_prompt, new_img_path))
            
            # 생성된 옵션들 나열 및 선택
            variants = sorted(list(img_dir.glob("*.png")))
            if variants:
                cols = st.columns(len(variants) if len(variants) <= 4 else 4)
                for idx, v_path in enumerate(variants):
                    with cols[idx % 4]:
                        st.image(str(v_path), use_container_width=True)
                        if st.button("이 이미지 선택", key=f"sel_{scene.scene_id}_{idx}"):
                            st.session_state.selected_assets.setdefault(scene.scene_id, {})["image"] = str(v_path)
                            scene.image_path = str(v_path)
                            # pipeline assembly를 위해 기본 경로로 복사
                            final_img_path = st.session_state.output_dir / "2_scenes" / f"scene_{scene.scene_id:03d}.png"
                            shutil.copy(v_path, final_img_path)
                            st.rerun()
            
            if selected_img:
                st.success(f"선택됨: {Path(selected_img).name}")
            else:
                all_images_selected = False
                st.warning("이미지를 생성하고 선택해주세요.")

    st.divider()
    if st.button("⬅️ 이전 단계 (음성 수정)"):
        st.session_state.step = 2
        st.rerun()

    if all_images_selected:
        if st.button("이미지 확정 및 비디오 생성 단계로 이동 ➡️", type="primary"):
            st.session_state.step = 4
            st.rerun()

# --- Step 4: 비디오 생성 전략 및 실행 ---
elif st.session_state.step == 4:
    st.header("Step 4: 🎥 비디오 생성 (AI Motion)")
    st.warning("비디오 생성은 토큰 소모가 크고 시간이 오래 걸립니다. 전략을 신중히 선택하세요.")
    
    video_strategy = st.radio(
        "생성 전략 선택",
        options=["none", "hybrid", "full"],
        format_func=lambda x: {
            "none": "이미지 + 줌팬 효과 (추가 비용 없음)",
            "hybrid": "일부 핵심 장면만 AI 비디오로 생성 (비용 효율적)",
            "full": "모든 장면을 AI 비디오(Veo)로 생성 (최고 품질, 고비용)"
        }[x]
    )
    settings.VEO_STRATEGY = video_strategy
    
    if st.button("비디오 생성 시작", type="primary"):
        with st.status("비디오를 생성 중입니다. 이 작업은 5~10분 정도 소요될 수 있습니다...") as status:
            asyncio.run(st.session_state.pipeline._generate_videos(st.session_state.script, st.session_state.output_dir))
            status.update(label="비디오 생성 완료!", state="complete")
        st.rerun()
    
    # 생성된 비디오 미리보기
    all_videos_done = True
    for scene in st.session_state.script.scenes:
        video_path = Path(st.session_state.output_dir / "4_videos" / f"scene_{scene.scene_id:03d}.mp4")
        if video_path.exists():
            with st.expander(f"Scene {scene.scene_id} 영상 확인", expanded=True):
                st.video(str(video_path))
        else:
            all_videos_done = False

    st.divider()
    if st.button("⬅️ 이전 단계 (이미지 재선택)"):
        st.session_state.step = 3
        st.rerun()

    if all_videos_done:
        if st.button("최종 조립 및 완성 ➡️", type="primary"):
            st.session_state.step = 5
            st.rerun()

# --- Step 5: 최종 조립 및 다운로드 ---
elif st.session_state.step == 5:
    st.header("Step 5: 🎬 최종 영상 완성")
    
    with st.spinner("마지막 조립 중..."):
        asyncio.run(st.session_state.pipeline._assemble_final_video(st.session_state.script, st.session_state.output_dir))
    
    final_video = st.session_state.output_dir / "final_video.mp4"
    if final_video.exists():
        st.balloons()
        st.video(str(final_video))
        
        with open(final_video, "rb") as f:
            st.download_button("최종 영상 다운로드", f, "final_educational_video.mp4", "video/mp4", use_container_width=True)
            
    st.divider()
    st.subheader("📦 생성된 자산 모음")
    # 자산 요약 표시...
    if st.button("새 프로젝트 시작"):
        reset_all()
