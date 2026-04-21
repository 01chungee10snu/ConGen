# 🎬 ConGen Pro: AI 교육 영상 자율 제작 프레임워크

**ConGen Pro**는 자연어 프롬프트 단 한 줄로 기획부터 대본 작성, 이미지 시각화, 음성 더빙, AI 비디오 모션, 그리고 배경음악(BGM) 믹싱까지 전 과정을 자율적으로 수행하는 **교육용 영상 제작 시스템**입니다.

최신 구글 멀티모달 생태계(Gemini 3.1, Veo 3.1, Nano Banana, Lyria)를 완벽하게 오케스트레이션하여, 비용 효율적이면서도 전문적인 결과물을 만들어냅니다.

---

## ✨ 주요 기능 (Key Features)

*   **전문가용 스토리보드 대시보드:** 직관적인 웹 UI(Streamlit)를 통해 장면별로 대사, 이미지, 영상을 미리보고 세밀하게 조율할 수 있습니다.
*   **비용 효율적인 초안 가조립 (Draft Play):** 비싼 AI 비디오를 만들기 전, 이미지와 음성만 결합한 줌팬(Zoom-pan) 영상으로 타이밍을 무료로 점검합니다.
*   **업계 최고 수준의 AI 모델 통합:**
    *   **대본 & 기획:** Gemini 3.1 Pro
    *   **이미지/슬라이드:** Nano Banana Pro (Gemini 3 Pro Image)
    *   **음성 (TTS):** Gemini 3.1 Flash TTS
    *   **비디오 모션:** Veo 3.1
    *   **배경음악 (BGM):** Lyria 3 Pro
*   **견고한 프로덕션 아키텍처:**
    *   비동기 FFmpeg 렌더링으로 멈춤 없는 고속 병렬 처리.
    *   파일 무결성 검증(0바이트 방지) 및 자동 자원 청소(Garbage Collection).
    *   환각(Hallucination) 방지 프롬프팅 및 오디오 팝 노이즈 제거(Fade) 적용.

---

## 🛠️ 사전 준비사항 (Prerequisites)

ConGen Pro를 실행하기 위해 컴퓨터에 다음 환경이 준비되어 있어야 합니다.

1.  **Python 3.10 이상** 설치
2.  **FFmpeg 설치 및 PATH 등록** (매우 중요)
    *   터미널에서 `ffmpeg -version` 및 `ffprobe -version` 입력 시 정상적으로 버전 정보가 출력되어야 합니다.
3.  **Google AI Studio API Key 발급**
    *   [Google AI Studio](https://aistudio.google.com/)에 접속하여 무료 API 키를 발급받으세요.

---

## 🚀 설치 및 설정 (Installation & Setup)

**1. 저장소 클론 및 디렉토리 이동**
```bash
git clone https://github.com/01chungee10snu/ConGen.git
cd ConGen
```

**2. 가상 환경 생성 및 활성화 (선택 사항이지만 권장)**
```bash
# Windows
python -m venv .venv
.\.venv\Scripts\activate

# macOS / Linux
python -m venv .venv
source .venv/bin/activate
```

**3. 필수 라이브러리 설치**
```bash
pip install --upgrade pip
pip install streamlit google-genai pydantic pydantic-settings python-dotenv tenacity Pillow
```

**4. 환경 변수 설정 (.env)**
프로젝트 루트 폴더에 `.env` 파일을 생성하고 발급받은 API 키를 입력합니다.
*(또는 앱을 실행한 후 웹 브라우저 화면의 사이드바에서 직접 입력할 수도 있습니다.)*
```env
GOOGLE_API_KEY=여러분의_API_키를_여기에_입력하세요
```

---

## 🎮 사용 방법 (How to Use)

모든 준비가 끝났습니다! 아래 명령어를 입력하여 **ConGen Director** 웹 앱을 실행합니다.

```bash
streamlit run streamlit_app.py
```

명령어를 실행하면 웹 브라우저가 열리며 전문적인 픽셀 아트 테마의 대시보드가 나타납니다.

### 🎬 단계별 워크플로우

1.  **초기 설정 (사이드바)**
    *   사이드바에서 **'API 상태 점검'** 버튼을 눌러 내 API 키가 정상인지, Veo 등 비디오 모델 권한이 있는지 확인합니다.
    *   **디테일 프롬프팅 제어**를 열어 영상의 화풍(예: 3D Render)이나 카메라 워크를 취향껏 설정합니다.
2.  **영상 기획 (Draft)**
    *   "중학생을 위한 블랙홀의 원리 (3개 장면)"처럼 원하는 주제를 입력하고 스크립트 생성을 시작합니다.
3.  **스토리보드 프로덕션 (Production)**
    *   **타임라인 뷰:** 각 장면별로 어떤 자산이 만들어졌는지 진행도를 확인합니다.
    *   **음성 & 이미지 생성:** 각 장면 카드를 열어 내레이션을 듣고, 이미지를 생성해 봅니다. 맘에 들지 않으면 텍스트를 고치고 다시 만들 수 있습니다.
    *   **초안 조립 (비용 $0):** 음성과 이미지가 준비되면 '초안 조립'을 눌러 타이밍이 맞는지 미리보기 영상을 확인합니다.
    *   **AI 비디오 생성:** 초안이 맘에 들면 '✨ 고품질 AI 비디오(Veo)' 버튼을 눌러 영상에 생명력을 불어넣습니다.
4.  **최종 마스터링 (Final Assembly)**
    *   모든 장면의 렌더링이 완료되면 맨 아래의 **'마스터링'** 버튼을 누릅니다.
    *   시스템이 자동으로 전체 길이를 계산하여 **Lyria BGM을 생성하고 부드럽게 믹싱**하여 최종 MP4 파일을 완성합니다. 다운로드하여 확인하세요!

---

## 🚨 자주 묻는 질문 (Troubleshooting)

**Q. `ffmpeg`를 찾을 수 없다는 오류가 납니다.**
A. 운영체제에 FFmpeg가 설치되지 않았거나 시스템 환경 변수(PATH)에 등록되지 않았습니다. FFmpeg를 설치한 후 터미널을 완전히 껐다가 다시 켜주세요.

**Q. API 상태 점검에서 'Leaked' 또는 'Permission Denied'가 뜹니다.**
A. GitHub 등 공개된 곳에 API 키가 포함된 파일(`.env` 등)이 올라가 구글이 키를 차단한 것입니다. AI Studio에서 기존 키를 삭제하고 새 키를 발급받아 교체하세요.

**Q. 비디오(Veo) 생성이 계속 실패합니다.**
A. 현재 계정에 Veo 모델 접근 권한이 없거나 할당량(Quota)을 초과했을 수 있습니다. 사이드바의 API 점검을 통해 권한을 확인하세요. 권한이 없다면 '초안 조립' 영상만으로도 훌륭한 영상을 렌더링할 수 있습니다.

---
*Built with ❤️ using Google Gemini & Streamlit*