# ConGen

ConGen은 자연어 주제를 입력받아 교육용 영상을 자동 생성하는 Python 기반 파이프라인입니다. 현재 저장소에 구현된 흐름은 다음과 같습니다.

1. Gemini로 장면별 스크립트 생성
2. Gemini 이미지 모델로 장면 이미지 생성
3. Gemini TTS로 장면별 내레이션 WAV 생성
4. Veo로 장면 비디오 생성, 또는 FFmpeg 정적 비디오 생성
5. FFmpeg로 최종 영상 병합

이 README는 현재 코드 기준으로 작성되었습니다. 상위 문서인 `IMPLEMENTATION_PLAN.md`, `교육 영상 제작 자동화 프레임워크 아이디어.md`에는 장기 계획과 아이디어가 포함되어 있으며, 그 내용이 모두 코드에 구현된 것은 아닙니다.

## 현재 구현 범위

- 스크립트 생성: `congen/agents/script_generator.py`
- 이미지 생성: `congen/agents/image_generator.py`
- 음성 생성: `congen/agents/audio_generator.py`
- 비디오 생성: `congen/agents/video_generator.py`
- 전체 오케스트레이션: `congen/pipeline.py`

현재 코드에서 실제로 사용하는 오디오 엔진은 ElevenLabs가 아니라 Google Gemini TTS입니다. 일부 로그 문자열과 기존 문서에 ElevenLabs라는 표현이 남아 있지만, 구현 기준으로는 Google API만으로 오디오를 생성합니다.

## 저장소 구조

```text
ConGen/
├─ main.py
├─ resume.py
├─ run_audio_generation.py
├─ run_video_generation.py
├─ run_assembly.py
├─ force_assembly.py
├─ run_santa_video.py
├─ congen/
│  ├─ agents/
│  ├─ config/
│  │  └─ prompts/
│  ├─ models/
│  └─ pipeline.py
├─ check/
├─ test/
├─ assets/
├─ output/
└─ temp/
```

## 사전 준비사항

### 1. 시스템 요구사항

- Python 3.10 이상 권장
- `ffmpeg`와 `ffprobe`가 설치되어 있고 PATH에 등록되어 있어야 함
- PowerShell 또는 일반 셸에서 `python`, `ffmpeg`, `ffprobe` 명령이 실행 가능해야 함

확인 예시:

```powershell
python --version
ffmpeg -version
ffprobe -version
```

### 2. Google API 준비

이 저장소는 `google-genai` SDK를 통해 Google 모델을 직접 호출합니다. 최소한 `GOOGLE_API_KEY`가 필요합니다.

- 필수: `GOOGLE_API_KEY`
- 선택: `GOOGLE_CLOUD_PROJECT`
- 선택: `VEO_STRATEGY`

현재 코드 기준 모델 사용처:

- 스크립트: `gemini-3-pro-preview`
- 이미지: `gemini-3-pro-image-preview`
- TTS: `gemini-2.5-flash-preview-tts`
- 비디오: `veo-3.1-fast-generate-preview`

준비 순서:

1. Google AI Studio 또는 현재 계정이 사용하는 Google GenAI 환경에서 API 키를 발급합니다.
2. 발급한 키가 텍스트, 이미지, TTS 모델 호출에 사용 가능한지 확인합니다.
3. Veo 모델을 쓸 예정이면 해당 계정에 비디오 생성 권한과 할당량이 있는지 확인합니다.
4. Veo 접근이 없거나 비용을 줄이고 싶다면 `VEO_STRATEGY=none`으로 설정합니다.

주의:

- `VEO_STRATEGY=none`이면 Veo 대신 FFmpeg로 정적 비디오를 만들어 전체 파이프라인을 끝까지 실행할 수 있습니다.
- `VEO_STRATEGY`의 주석에는 `full`, `hybrid`, `minimal`, `none`이 적혀 있지만, 현재 코드에서 분기 구현이 명확한 값은 사실상 `none`과 그 외 값뿐입니다.
- `GOOGLE_CLOUD_PROJECT`는 설정 클래스에서 받지만 현재 구현에서는 직접 사용하지 않습니다.

### 3. 환경 변수 파일 준비

프로젝트 루트에 `.env` 파일을 만듭니다.

```env
GOOGLE_API_KEY=your_google_api_key

# 선택 사항
GOOGLE_CLOUD_PROJECT=your_project_id

# full: Veo 사용, none: FFmpeg 정적 비디오 사용
VEO_STRATEGY=none

# 현재 코드에서는 사용하지 않음
# ELEVENLABS_API_KEY=
```

보안 주의:

- 실제 API 키가 들어있는 `.env`는 커밋하지 않는 것을 권장합니다.
- 기존 `.env`가 있다면 새 키를 덮어쓰기 전에 백업 여부를 확인하세요.

## 의존성

### Python 패키지

현재 코드 import 기준 필수 패키지:

- `google-genai`
- `pydantic`
- `pydantic-settings`
- `python-dotenv`
- `tenacity`

선택 패키지:

- `Pillow`
  - `congen/agents/video_generator.py`의 단독 테스트 블록에서만 사용
  - 전체 파이프라인 실행에는 필수 아님

### 외부 도구

- `ffmpeg`
- `ffprobe`

## 설치 방법

PowerShell 기준 예시입니다.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install google-genai pydantic pydantic-settings python-dotenv tenacity Pillow
```

그 다음 프로젝트 루트에 `.env`를 작성합니다.

## 실행 전 점검

저장소에는 간단한 점검 스크립트가 포함되어 있습니다.

```powershell
python .\check\20251212114500_setup_check.py
python .\check\20251212113602_model_list_check.py
python .\check\20251212113600_api_access_check.py
```

용도:

- `setup_check.py`: 설정 로드와 기본 import 확인
- `model_list_check.py`: 계정에서 보이는 모델 목록 확인
- `api_access_check.py`: 텍스트, 이미지, 비디오 호출 가능 여부 점검

Veo 권한이나 할당량만 따로 보고 싶다면:

```powershell
python .\test\check_veo_quota.py
```

## 사용 방법

### 1. 전체 파이프라인 실행

현재 `main.py`는 CLI 인자를 받지 않고, 파일 내부의 `topic` 문자열을 직접 수정해서 사용합니다.

```powershell
python .\main.py
```

실행 흐름:

1. `output/YYYYMMDD_HHMMSS_<topic>/` 디렉터리 생성
2. `1_script.json` 저장
3. `2_scenes/`에 이미지 생성
4. `3_audio/`에 WAV 생성
5. `4_videos/`에 MP4 생성
6. `final_video.mp4` 생성

### 2. 출력 결과 구조

```text
output/
└─ 20251216_165148_ConGen_프로젝트_소개_교육_영상을_자동으로_생성하/
   ├─ 1_script.json
   ├─ 2_scenes/
   │  ├─ scene_001.png
   │  └─ ...
   ├─ 3_audio/
   │  ├─ scene_001.wav
   │  └─ ...
   ├─ 4_videos/
   │  ├─ scene_001.mp4
   │  └─ ...
   ├─ temp/
   └─ final_video.mp4
```

### 3. 실패 후 이어서 실행

최근 생성된 `output` 폴더를 기준으로 재개합니다.

```powershell
python .\resume.py
```

현재 `resume.py`는 다음만 수행합니다.

- 기존 `1_script.json` 로드
- 비디오 생성 재시도
- 최종 합성 재시도

즉, 오디오가 아직 없는 상태라면 먼저 `run_audio_generation.py`를 실행해야 합니다.

### 4. 오디오만 다시 생성

```powershell
python .\run_audio_generation.py
```

동작:

- 가장 최근 `output` 폴더 탐색
- `1_script.json`에서 narration 읽기
- `3_audio/`에 WAV 생성

주의:

- 파일 안의 출력 메시지에는 `ElevenLabs`라고 적혀 있지만, 실제 호출은 `AudioGeneratorAgent`의 Gemini TTS입니다.

### 5. 비디오 생성만 다시 실행

```powershell
python .\run_video_generation.py
```

실제 동작은 `resume.py`와 거의 동일합니다. 즉, 최신 결과 폴더에서 비디오 생성과 최종 합성까지 다시 시도합니다.

### 6. 최종 합성만 다시 실행

```powershell
python .\run_assembly.py
```

주의:

- 현재 `run_assembly.py`는 `scene_001`부터 `scene_005`까지만 순회하도록 작성되어 있습니다.
- 씬이 6개 이상인 프로젝트에서는 전체 씬을 다 합치지 못할 수 있습니다.
- 전체 씬 기준으로 다시 합치려면 `resume.py` 경로를 쓰거나 `force_assembly.py`를 수정해서 사용하는 편이 안전합니다.

### 7. 특정 output 폴더 강제 합성

```powershell
python .\force_assembly.py
```

실행 전에 파일 안의 `target_dir_name` 값을 원하는 폴더명으로 수정해야 합니다.

### 8. 샘플 프로젝트 실행

`run_santa_video.py`는 `santa/` 폴더의 이미지를 사용해 별도 시나리오를 구성하는 예제 스크립트입니다.

```powershell
python .\run_santa_video.py
```

## 주요 설정

핵심 설정은 `congen/config/settings.py`에서 관리합니다.

자주 보는 항목:

- `GOOGLE_API_KEY`
- `GOOGLE_CLOUD_PROJECT`
- `MODEL_GEMINI_PRO`
- `MODEL_IMAGEN`
- `MODEL_VEO`
- `VEO_STRATEGY`
- `OUTPUT_DIR`
- `TEMP_DIR`
- `ASSETS_DIR`

실무적으로 가장 중요한 값은 `VEO_STRATEGY`입니다.

- `full`
  - 기본값
  - Veo 비디오 생성을 시도
  - 실패 시 정적 비디오로 폴백
- `none`
  - Veo를 건너뛰고 FFmpeg로 정적 비디오 생성
  - API 권한이 부족하거나 비용을 줄이고 싶을 때 유용

## Google API 준비 방법 상세

추천 절차는 다음과 같습니다.

1. Google AI Studio에서 API 키를 발급합니다.
2. `.env`에 `GOOGLE_API_KEY`를 설정합니다.
3. `python .\check\20251212113602_model_list_check.py`로 계정에서 보이는 모델 목록을 확인합니다.
4. `python .\check\20251212113600_api_access_check.py`로 실제 호출 가능 여부를 확인합니다.
5. Veo가 막혀 있으면 우선 `VEO_STRATEGY=none`으로 개발과 파이프라인 검증을 진행합니다.
6. Veo 접근이 필요해지면 계정 권한, 미리보기 접근 여부, 할당량 상태를 다시 점검합니다.

이 프로젝트는 현재 Vertex AI 전용 인증 흐름이 아니라 API 키 기반 호출에 맞춰져 있습니다.

## 자주 발생하는 문제

### `GOOGLE_API_KEY is not set`

- `.env` 파일이 프로젝트 루트에 있는지 확인
- `GOOGLE_API_KEY=...` 형식으로 들어있는지 확인
- 가상환경을 바꿨다면 다시 실행

### `ffmpeg` 또는 `ffprobe`를 찾을 수 없음

- FFmpeg를 설치하고 PATH에 추가
- 새 셸을 열어서 `ffmpeg -version`, `ffprobe -version` 재확인

### 이미지 또는 비디오 모델 호출 실패

- 계정에 해당 모델 권한이 없는 경우가 많음
- 먼저 점검 스크립트로 접근 가능 여부 확인
- 개발 중에는 `VEO_STRATEGY=none`으로 우회 가능

### 중간 실패 후 다시 돌리고 싶음

일반적인 복구 순서:

1. 오디오가 없으면 `python .\run_audio_generation.py`
2. 비디오와 최종 합성은 `python .\resume.py`

### 로그상 ElevenLabs가 보임

- 현재 구현은 Google Gemini TTS를 사용
- 로그 문구가 오래된 상태일 뿐 실제 의존성은 Google 쪽입니다

## 참고 문서

- `IMPLEMENTATION_PLAN.md`: 장기 구현 계획과 아키텍처 초안
- `교육 영상 제작 자동화 프레임워크 아이디어.md`: 조사/아이디어 문서
- `check/`: API 및 모델 접근 점검용 스크립트
- `test/`: 단일 기능 테스트 및 실험 스크립트
