
import streamlit as st
import asyncio
import json
import os
import shutil
from pathlib import Path
from dotenv import load_dotenv
import logging

from congen.pipeline import VideoGenerationPipeline, get_media_duration
from congen.config.settings import settings
from congen.models.script import Script

# 페이지 설정
st.set_page_config(
    page_title="ConGen Director - Pixel Edition",
    page_icon="👾",
    layout="wide"
)

# --- 전문적인 모노톤 픽셀 아트 CSS 주입 ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DotGothic16&family=Silkscreen:wght@400;700&display=swap');

    /* 전체 배경 및 폰트 설정 */
    .stApp {
        background-color: #121212;
        color: #E0E0E0;
        font-family: 'Monospace', 'Courier New', Courier, monospace;
    }

    /* 헤더 및 타이틀 */
    h1, h2, h3 {
        font-family: 'Silkscreen', cursive !important;
        text-transform: uppercase;
        letter-spacing: 2px;
        color: #FFFFFF !important;
    }

    /* 픽셀 테두리 컨테이너 */
    div[data-testid="stVerticalBlock"] > div[style*="border"] {
        border: 4px solid #444444 !important;
        background-color: #1A1A1A !important;
        box-shadow: 4px 4px 0px #000000;
        padding: 20px !important;
        image-rendering: pixelated;
    }

    /* 버튼 스타일 (픽셀 스타일) */
    .stButton > button {
        font-family: 'Silkscreen', cursive !important;
        background-color: #333333 !important;
        color: #FFFFFF !important;
        border: 4px solid #555555 !important;
        border-radius: 0px !important;
        box-shadow: 4px 4px 0px #000000 !important;
        transition: all 0.1s;
    }

    .stButton > button:hover {
        background-color: #555555 !important;
        transform: translate(-2px, -2px);
        box-shadow: 6px 6px 0px #000000 !important;
    }

    .stButton > button:active {
        transform: translate(2px, 2px);
        box-shadow: 0px 0px 0px #000000 !important;
    }

    /* 사이드바 스타일 */
    [data-testid="stSidebar"] {
        background-color: #0A0A0A !important;
        border-right: 4px solid #333333;
    }

    /* 입력창 스타일 */
    .stTextArea textarea, .stTextInput input {
        background-color: #1A1A1A !important;
        color: #00FF41 !important; /* 매트릭스 느낌의 강조색 (선택적) */
        border: 2px solid #444444 !important;
        font-family: 'DotGothic16', sans-serif !important;
    }

    /* 진행 바 */
    .stProgress > div > div > div > div {
        background-color: #E0E0E0 !important;
        border-radius: 0px !important;
    }

    /* 스캔라인 효과 (배경) */
    .stApp::before {
        content: " ";
        display: block;
        position: absolute;
        top: 0; left: 0; bottom: 0; right: 0;
        background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06));
        z-index: 2;
        background-size: 100% 2px, 3px 100%;
        pointer-events: none;
    }
    
    /* 카드 가독성 개선 */
    .stAlert {
        border-radius: 0px !important;
        border: 2px solid #444444 !important;
        background-color: #222222 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- 세션 상태 관리 ---
if "pipeline" not in st.session_state:
    st.session_state.pipeline = VideoGenerationPipeline()
if "step" not in st.session_state:
    st.session_state.step = "draft"  # draft, production, final
if "script" not in st.session_state:
    st.session_state.script = None
if "output_dir" not in st.session_state:
    st.session_state.output_dir = None
if "processing_status" not in st.session_state:
    st.session_state.processing_status = {} # {scene_id: {audio: bool, image: bool, draft: bool, video: bool}}

def reset_all():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# --- 사이드바: 컨트롤 타워 ---
with st.sidebar:
    st.title("🎬 ConGen Director")
    st.markdown("---")
    
    # 1. 모델 설정
    st.subheader("🤖 AI 모델 설정")
    with st.expander("모델 변경"):
        settings.MODEL_GEMINI_PRO = st.selectbox("스크립트", list(settings.TEXT_MODELS.values()), index=0)
        settings.MODEL_IMAGEN = st.selectbox("이미지", list(settings.IMAGE_MODELS.values()), index=0)
        settings.MODEL_VEO = st.selectbox("비디오", list(settings.VIDEO_MODELS.values()), index=0)
        settings.MODEL_TTS = st.selectbox("음성(TTS)", list(settings.AUDIO_MODELS.values())[1:], index=0)
        settings.MODEL_MUSIC = st.selectbox("배경음악(BGM)", list(settings.AUDIO_MODELS.values())[:1], index=0)
    
    # 2. API 점검
    user_api_key = st.text_input("Google API Key", value=os.getenv("GOOGLE_API_KEY", ""), type="password")
    if user_api_key: os.environ["GOOGLE_API_KEY"] = user_api_key
    
    if st.button("🔍 API 상태 점검", use_container_width=True):
        if not user_api_key:
            st.error("API 키를 먼저 입력해주세요.")
        else:
            with st.status("API 연결 및 모델 권한 확인 중...") as status:
                from google import genai
                try:
                    temp_client = genai.Client(api_key=user_api_key)
                    
                    # 1. 텍스트 (Gemini)
                    try:
                        models = temp_client.models.list()
                        model_names = [m.name for m in models]
                        
                        if any("gemini" in name.lower() for name in model_names):
                            st.success("✅ Gemini (Text/Script): OK")
                        else:
                            st.warning("⚠️ Gemini (Text): Not found in list")
                    except Exception as e:
                        st.error(f"❌ Gemini API: Error - {str(e)[:50]}...")
                    
                    # 2. 이미지 (Nano Banana)
                    if any("gemini-3-pro-image" in name.lower() for name in model_names):
                        st.success("✅ Nano Banana (Image): OK")
                    else:
                        st.warning("⚠️ Nano Banana (Image): Not found in list")
                    
                    # 3. 비디오 (Veo)
                    if any("veo" in name.lower() for name in model_names):
                        st.success("✅ Veo (Video): OK")
                    else:
                        st.warning("⚠️ Veo (Video): Not found in list")
                        
                    status.update(label="API 점검 완료", state="complete")
                except Exception as e:
                    st.error(f"연결 실패: {e}")
                    status.update(label="API 점검 실패", state="error")

    st.markdown("---")
    if st.button("🔄 새 프로젝트 시작", use_container_width=True):
        reset_all()

# --- 메인 워크플로우 ---

# [단계 1] 주제 입력 및 초안 생성
if st.session_state.step == "draft":
    st.title("📝 1. 영상 기획 및 초안 작성")
    topic = st.text_area("제작하고 싶은 교육 영상의 주제를 입력하세요", placeholder="예: 중학생을 위한 인플레이션의 원리 (3개 장면)", height=150)
    
    if st.button("스크립트 생성 시작 🚀", type="primary"):
        with st.spinner("AI가 교육 시나리오를 설계 중입니다..."):
            output_dir = st.session_state.pipeline._create_output_dir(topic)
            script = asyncio.run(st.session_state.pipeline.script_agent.run(topic))
            st.session_state.script = script
            st.session_state.output_dir = output_dir
            st.session_state.step = "production"
            st.rerun()

# [단계 2] 스토리보드 대시보드 (핵심 UI)
elif st.session_state.step == "production":
    st.title("🎨 2. 스토리보드 & 프로덕션")
    st.markdown("각 장면의 음성과 이미지를 확인하고, AI 비디오를 만들기 전 '초안 영상'으로 리듬을 체크하세요.")

    # 전체 요약 정보
    meta = st.session_state.script.metadata
    st.info(f"📌 **제목:** {meta.title} | **학습목표:** {meta.learning_objective}")

    # 장면별 스토리보드 카드
    for i, scene in enumerate(st.session_state.script.scenes):
        scene_id = scene.scene_id
        with st.container(border=True):
            st.subheader(f"🎬 Scene {scene_id}")
            
            # 3단 컬럼 구성: [텍스트/음성] | [이미지] | [미리보기/비디오]
            col_text, col_img, col_prev = st.columns([1.5, 1.2, 1.3])
            
            with col_text:
                st.markdown("**🖋️ 스크립트 & 음성**")
                scene.audio.narration = st.text_area("내레이션", scene.audio.narration, key=f"narr_{scene_id}", height=100)
                
                audio_path = st.session_state.output_dir / "3_audio" / f"scene_{scene_id:03d}.wav"
                if st.button(f"🔊 음성 생성/미리듣기", key=f"btn_aud_{scene_id}"):
                    with st.spinner("생성 중..."):
                        asyncio.run(st.session_state.pipeline.audio_agent.run(scene.audio.narration, audio_path))
                
                if audio_path.exists():
                    st.audio(str(audio_path))
                    scene.audio_path = str(audio_path)
                else:
                    st.caption("음성이 아직 생성되지 않았습니다.")

            with col_img:
                st.markdown("**🖼️ 이미지 생성**")
                scene.visual.description = st.text_area("이미지 묘사", scene.visual.description, key=f"img_desc_{scene_id}", height=100)
                
                img_path = st.session_state.output_dir / "2_scenes" / f"scene_{scene_id:03d}.png"
                if st.button(f"🎨 이미지 생성/미리보기", key=f"btn_img_{scene_id}"):
                    with st.spinner("그리는 중..."):
                        enhanced_prompt = f"Educational illustration, high quality, 4k, {scene.visual.description}"
                        asyncio.run(st.session_state.pipeline.image_agent.run(enhanced_prompt, img_path))
                
                if img_path.exists():
                    st.image(str(img_path), use_container_width=True)
                    scene.image_path = str(img_path)
                else:
                    st.caption("이미지가 아직 생성되지 않았습니다.")

            with col_prev:
                st.markdown("**📺 영상 미리보기 & AI Motion**")
                
                # 초안 영상 (Draft Video - Ken Burns) 생성 버튼
                draft_path = st.session_state.output_dir / "temp" / f"draft_{scene_id:03d}.mp4"
                if st.button(f"🎞️ 초안 영상(줌팬) 미리보기", key=f"btn_draft_{scene_id}", disabled=not (audio_path.exists() and img_path.exists())):
                    with st.spinner("초안 조립 중..."):
                        # FFmpeg 줌팬 효과 적용
                        st.session_state.pipeline._create_static_video(img_path, audio_path, draft_path)
                
                if draft_path.exists():
                    st.video(str(draft_path))
                    st.caption("초안 영상 (비용 $0)")
                    
                    # AI 비디오(Veo) 생성 버튼 - 신중한 선택 유도
                    video_path = st.session_state.output_dir / "4_videos" / f"scene_{scene_id:03d}.mp4"
                    if st.button(f"✨ AI 비디오 생성 (Veo)", key=f"btn_veo_{scene_id}", type="secondary"):
                        with st.spinner("AI가 영상을 생성 중입니다 (약 2~3분 소요)..."):
                            asyncio.run(st.session_state.pipeline.video_agent.run(scene.visual.description, img_path, video_path))
                    
                    if video_path.exists():
                        st.video(str(video_path))
                        st.success("AI 비디오 완료!")
                        scene.video_path = str(video_path)
                    else:
                        # AI 비디오가 없으면 초안 영상을 최종 소스로 사용하도록 설정
                        scene.video_path = str(draft_path)
                else:
                    st.warning("음성과 이미지가 준비되면 미리보기가 가능합니다.")

    # 전체 조립 단계로 이동
    st.divider()
    col_left, col_right = st.columns([1, 1])
    with col_right:
        if st.button("모든 장면 확정 및 최종 영상 조립 ➡️", type="primary", use_container_width=True):
            # 스크립트 최종본 저장
            script_path = st.session_state.output_dir / "1_script.json"
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(st.session_state.script.model_dump(), indent=2, ensure_ascii=False))
            st.session_state.step = "final"
            st.rerun()

# [단계 3] 최종 조립 및 배포
elif st.session_state.step == "final":
    st.header("🎬 3. 최종 영상 렌더링")
    
    with st.spinner("모든 클립을 하나의 고화질 영상으로 조립하고 있습니다..."):
        asyncio.run(st.session_state.pipeline._assemble_final_video(st.session_state.script, st.session_state.output_dir))
    
    final_video = st.session_state.output_dir / "final_video.mp4"
    if final_video.exists():
        st.balloons()
        st.video(str(final_video))
        
        with open(final_video, "rb") as f:
            st.download_button("최종 영상 다운로드 (.mp4)", f, f"congen_{meta.title}.mp4", "video/mp4", use_container_width=True)
            
    if st.button("⬅️ 스토리보드로 돌아가 수정하기"):
        st.session_state.step = "production"
        st.rerun()
