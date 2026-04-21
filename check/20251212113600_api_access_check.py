"""
ConGen API 접근 권한 테스트 스크립트
- Gemini 3 Pro (텍스트 생성)
- Nano Banana Pro / Gemini 3 Pro Image (이미지 생성)
- Veo 3.1 (비디오 생성)
"""

import os
import sys
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

def test_gemini_api():
    """Gemini API 연결 및 모델 접근 테스트"""
    print("\n" + "="*60)
    print("🔍 1. Gemini API 연결 테스트")
    print("="*60)
    
    try:
        from google import genai
        from google.genai import types
        
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("❌ GOOGLE_API_KEY 환경 변수가 설정되지 않았습니다.")
            return False
        
        print(f"   API Key: {api_key[:10]}...{api_key[-5:]}")
        
        # 클라이언트 초기화
        client = genai.Client(api_key=api_key)
        print("   ✅ genai.Client 초기화 성공")
        
        # 사용 가능한 모델 목록 확인
        print("\n📋 사용 가능한 모델 목록:")
        try:
            models = client.models.list()
            model_names = []
            for model in models:
                model_names.append(model.name)
                # 관심 모델만 표시
                if any(keyword in model.name.lower() for keyword in ['gemini-3', 'veo', 'imagen']):
                    print(f"   ⭐ {model.name}")
                elif 'gemini' in model.name.lower():
                    print(f"      {model.name}")
            
            # 핵심 모델 확인
            print("\n🎯 핵심 모델 접근 가능 여부:")
            target_models = [
                ('gemini-3-pro', 'Gemini 3 Pro (텍스트)'),
                ('gemini-3-pro-preview', 'Gemini 3 Pro Preview'),
                ('gemini-2.0-flash', 'Gemini 2.0 Flash (폴백)'),
                ('gemini-2.5-flash', 'Gemini 2.5 Flash'),
                ('gemini-3-pro-image', 'Nano Banana Pro (이미지)'),
                ('veo-3.1', 'Veo 3.1 (비디오)'),
                ('imagen-3', 'Imagen 3 (이미지 폴백)'),
            ]
            
            for model_id, description in target_models:
                found = any(model_id in name.lower() for name in model_names)
                status = "✅" if found else "❌"
                print(f"   {status} {description} ({model_id})")
                
        except Exception as e:
            print(f"   ⚠️ 모델 목록 조회 실패: {e}")
        
        return True
        
    except ImportError as e:
        print(f"❌ google-genai 패키지 import 실패: {e}")
        print("   설치: pip install google-genai")
        return False
    except Exception as e:
        print(f"❌ API 연결 실패: {e}")
        return False


def test_text_generation():
    """텍스트 생성 테스트"""
    print("\n" + "="*60)
    print("🔍 2. 텍스트 생성 테스트 (Gemini)")
    print("="*60)
    
    try:
        from google import genai
        
        api_key = os.getenv("GOOGLE_API_KEY")
        client = genai.Client(api_key=api_key)
        
        # 사용 가능한 모델로 테스트
        test_models = [
            'gemini-3-pro-preview',
            'gemini-2.5-flash-preview-05-20',
            'gemini-2.0-flash',
            'gemini-1.5-flash',
        ]
        
        for model_name in test_models:
            try:
                print(f"\n   테스트 모델: {model_name}")
                response = client.models.generate_content(
                    model=model_name,
                    contents="안녕하세요. 간단한 테스트입니다. '테스트 성공'이라고 답해주세요."
                )
                print(f"   ✅ 응답: {response.text[:100]}...")
                return True
            except Exception as e:
                print(f"   ❌ {model_name} 실패: {str(e)[:80]}")
                continue
        
        print("   ❌ 모든 모델 테스트 실패")
        return False
        
    except Exception as e:
        print(f"❌ 텍스트 생성 테스트 실패: {e}")
        return False


def test_image_generation():
    """이미지 생성 테스트 (Nano Banana Pro / Imagen)"""
    print("\n" + "="*60)
    print("🔍 3. 이미지 생성 테스트 (Nano Banana Pro / Imagen)")
    print("="*60)
    
    try:
        from google import genai
        from google.genai import types
        
        api_key = os.getenv("GOOGLE_API_KEY")
        client = genai.Client(api_key=api_key)
        
        # 이미지 생성 모델 테스트
        test_models = [
            'gemini-3-pro-image',
            'imagen-3.0-generate-002',
            'imagen-3.0-generate-001',
        ]
        
        for model_name in test_models:
            try:
                print(f"\n   테스트 모델: {model_name}")
                
                # Imagen 모델용
                if 'imagen' in model_name:
                    response = client.models.generate_images(
                        model=model_name,
                        prompt="A simple red circle on white background, minimal, clean",
                        config=types.GenerateImagesConfig(
                            number_of_images=1,
                        )
                    )
                else:
                    # Gemini 이미지 생성 모델용
                    response = client.models.generate_content(
                        model=model_name,
                        contents="Generate an image of a simple red circle on white background",
                        config=types.GenerateContentConfig(
                            response_modalities=["IMAGE"]
                        )
                    )
                
                print(f"   ✅ 이미지 생성 성공!")
                return True
                
            except Exception as e:
                error_msg = str(e)
                if "not found" in error_msg.lower() or "does not exist" in error_msg.lower():
                    print(f"   ❌ 모델 없음: {model_name}")
                elif "permission" in error_msg.lower() or "access" in error_msg.lower():
                    print(f"   ⚠️ 접근 권한 없음: {model_name}")
                else:
                    print(f"   ❌ {model_name} 실패: {error_msg[:80]}")
                continue
        
        print("   ❌ 이미지 생성 모델 접근 불가")
        return False
        
    except Exception as e:
        print(f"❌ 이미지 생성 테스트 실패: {e}")
        return False


def test_video_generation():
    """비디오 생성 테스트 (Veo 3.1)"""
    print("\n" + "="*60)
    print("🔍 4. 비디오 생성 테스트 (Veo 3.1)")
    print("="*60)
    
    try:
        from google import genai
        from google.genai import types
        
        api_key = os.getenv("GOOGLE_API_KEY")
        client = genai.Client(api_key=api_key)
        
        # Veo 모델 테스트
        test_models = [
            'veo-3.1-generate-001',
            'veo-3.1-fast-generate-001',
            'veo-3-generate-001',
            'veo-2.0-generate-001',
        ]
        
        for model_name in test_models:
            try:
                print(f"\n   테스트 모델: {model_name}")
                
                # 비디오 생성 요청 (실제 생성하지 않고 접근 가능 여부만 확인)
                # 비용 절약을 위해 실제 생성은 하지 않음
                operation = client.models.generate_videos(
                    model=model_name,
                    prompt="A simple test animation, minimal, 1 second",
                    config=types.GenerateVideosConfig(
                        aspect_ratio="16:9",
                        duration_seconds=1,  # 최소 길이
                    )
                )
                
                print(f"   ✅ Veo API 접근 성공! (Operation 시작됨)")
                print(f"   ⚠️ 비용 절약을 위해 결과 대기 없이 종료")
                return True
                
            except Exception as e:
                error_msg = str(e)
                if "not found" in error_msg.lower() or "does not exist" in error_msg.lower():
                    print(f"   ❌ 모델 없음: {model_name}")
                elif "permission" in error_msg.lower() or "access" in error_msg.lower():
                    print(f"   ⚠️ 접근 권한 없음 (Paid Preview 필요): {model_name}")
                elif "quota" in error_msg.lower():
                    print(f"   ⚠️ 할당량 초과: {model_name}")
                else:
                    print(f"   ❌ {model_name} 실패: {error_msg[:100]}")
                continue
        
        print("\n   ℹ️ Veo 3.1은 Paid Preview입니다.")
        print("      접근하려면 Google AI Studio에서 대기자 신청이 필요합니다.")
        print("      https://aistudio.google.com")
        return False
        
    except Exception as e:
        print(f"❌ 비디오 생성 테스트 실패: {e}")
        return False


def print_summary(results):
    """테스트 결과 요약"""
    print("\n" + "="*60)
    print("📊 API 접근 권한 테스트 결과 요약")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ 성공" if passed else "❌ 실패/미접근"
        print(f"   {test_name}: {status}")
    
    print("\n" + "-"*60)
    
    if all(results.values()):
        print("🎉 모든 API 접근 가능! Full Veo 전략 진행 가능합니다.")
    elif results.get("Gemini API 연결") and results.get("텍스트 생성"):
        print("⚠️ 기본 API는 사용 가능합니다.")
        if not results.get("이미지 생성"):
            print("   - 이미지 생성: Nano Banana Pro 또는 Imagen 접근 신청 필요")
        if not results.get("비디오 생성"):
            print("   - 비디오 생성: Veo 3.1 Paid Preview 신청 필요")
        print("\n📝 권장 조치:")
        print("   1. Google AI Studio 접속: https://aistudio.google.com")
        print("   2. Waitlist 신청 (Veo, Imagen 등)")
        print("   3. 또는 Vertex AI에서 직접 API 활성화")
    else:
        print("❌ API 접근에 문제가 있습니다.")
        print("   1. API 키가 올바른지 확인하세요.")
        print("   2. Google AI Studio에서 새 API 키 발급을 고려하세요.")
        print("      https://aistudio.google.com/apikey")


def main():
    print("="*60)
    print("🚀 ConGen API 접근 권한 테스트")
    print("="*60)
    print(f"   Python 버전: {sys.version}")
    print(f"   작업 디렉토리: {os.getcwd()}")
    
    results = {}
    
    # 1. Gemini API 연결 테스트
    results["Gemini API 연결"] = test_gemini_api()
    
    # 2. 텍스트 생성 테스트
    results["텍스트 생성"] = test_text_generation()
    
    # 3. 이미지 생성 테스트
    results["이미지 생성"] = test_image_generation()
    
    # 4. 비디오 생성 테스트
    results["비디오 생성"] = test_video_generation()
    
    # 결과 요약
    print_summary(results)


if __name__ == "__main__":
    main()
