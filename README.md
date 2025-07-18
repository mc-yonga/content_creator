# 광고 웹툰 콘텐츠 생성기

LangChain과 Pydantic을 활용한 광고 웹툰 콘텐츠 자동 생성 도구입니다.

## 🚀 주요 기능

1. **18개 씬 자동 생성**: 광고 스크립트를 입력하면 자연스럽게 연결된 18개 씬을 생성
2. **AI 이미지 생성**: DALL-E를 이용해 각 씬의 웹툰 스타일 이미지 생성
3. **웹 인터페이스**: Streamlit 기반의 사용자 친화적 인터페이스
4. **Rate Limit 처리**: OpenAI API 제한사항을 자동으로 처리

## 📋 파일 구조

### 핵심 모듈
- `models.py`: Pydantic 모델 정의 (Scene, ScenesDocument)
- `sceneCreator.py`: LangChain을 이용한 씬 생성 에이전트
- `imgCreator.py`: DALL-E를 이용한 이미지 생성 모듈
- `main.py`: 커맨드라인 인터페이스

### Streamlit 웹 앱
- `streamlit_app.py`: 메인 웹 애플리케이션
- `streamlit_image_handler.py`: 이미지 생성 진행률 추적
- `streamlit_gallery.py`: 이미지 갤러리 및 다운로드
- `streamlit_utils.py`: 유틸리티 함수 및 에러 처리

## 🛠️ 설치 및 설정

### 1. 필요한 패키지 설치
```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정
`.env` 파일을 생성하고 OpenAI API 키를 설정:
```
OPENAI_API_KEY=your_openai_api_key_here
```

## 🎯 사용 방법

### 웹 인터페이스 (권장)
```bash
streamlit run streamlit_app.py
```

웹 브라우저에서 다음 단계를 따르세요:
1. **프롬프트 입력**: 광고 웹툰용 스크립트 입력
2. **씬 생성**: 18개 씬 자동 생성 및 확인
3. **이미지 생성**: 개별 또는 전체 이미지 생성
4. **결과 확인**: 갤러리에서 결과 확인 및 다운로드

### 커맨드라인 인터페이스
```bash
# 씬 생성
python3 sceneCreator.py "your_prompt_here" output_scenes.json

# 이미지 생성 (단일)
python3 imgCreator.py output_scenes.json 1 images/

# 이미지 생성 (전체)
python3 imgCreator.py output_scenes.json images/
```

## 🎨 씬 생성 규칙

- **홀수 씬 (1,3,5,7,9,11,13,15,17)**: 미완성 문장 ("~는데", "~해서", "~더니", "~니까")
- **짝수 씬 (2,4,6,8,10,12,14,16,18)**: 완성 문장 ("~더라고요", "~네요", "~겠어요?", "~세요")

이 규칙으로 자연스럽게 연결되는 대화체 스크립트가 생성됩니다.

## ⚡ API 제한사항

- **DALL-E API**: 분당 5회 요청 제한
- **자동 대기**: 12초 간격으로 순차 생성
- **전체 생성 시간**: 약 3-4분 소요

## 📁 출력 파일

- `scenes_YYYYMMDD_HHMMSS.json`: 생성된 씬 데이터
- `generated_images/`: 생성된 이미지 폴더
- `scene_X_YYYYMMDD_HHMMSS.png`: 개별 씬 이미지

## 🔧 커스터마이징

### 모델 변경
```python
# sceneCreator.py에서 모델 변경
result = create_scenes(user_prompt, model="gpt-4o")  # 또는 gpt-3.5-turbo
```

### 이미지 설정 변경
```python
# imgCreator.py에서 이미지 설정 변경
generate_scene_image(
    quality="hd",        # standard 또는 hd
    size="1792x1024",   # 1024x1024, 1792x1024, 1024x1792
    style="natural"      # vivid 또는 natural
)
```

## 🐛 문제 해결

### 일반적인 오류
1. **ModuleNotFoundError**: `pip install -r requirements.txt` 실행
2. **API 키 오류**: `.env` 파일의 `OPENAI_API_KEY` 확인
3. **Rate Limit 오류**: 자동으로 처리되며, 12초씩 대기

### 로그 확인
- Streamlit 앱: 웹 인터페이스에서 실시간 로그 확인
- 커맨드라인: 터미널 출력으로 상태 확인

## 📚 예시

### 입력 프롬프트 예시
```
눈 앞에 날파리가 떠다니는 거슬리는 비문증, 2주만에 싹 말끔해질 줄 누가 알았겠어요?
비문증 방치하면 실명될 수도 있다고 해서 치료 받아야하나 하던 차에 친구가 이거 한번 먹어보라 하더라고요.
그냥 하루에 한 알씩 챙겨 먹기 시작했는데 날파리 갯수가 점점 줄어들면서 시야가 맑아지는게 느껴지더라고요.
```

### 출력 예시
```json
{
  "scenes": {
    "scene_1": {
      "script": "요즘 눈 앞에 날파리 같은 게 자꾸 떠다녀서",
      "main_keyword": "비문증증상 날파리떠다님 시야방해"
    },
    "scene_2": {
      "script": "정말 거슬리더라고요.",
      "main_keyword": "불편표정 눈비비기 스트레스"
    }
  }
}
```

## 🎉 완료!

모든 컴포넌트가 성공적으로 통합되었습니다. 광고 웹툰 제작을 시작해보세요!