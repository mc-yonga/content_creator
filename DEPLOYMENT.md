# Railway 배포 가이드

## 🚀 Railway로 배포하기

### 1. Railway 계정 및 프로젝트 생성
1. [Railway.app](https://railway.app)에서 계정 생성
2. GitHub 리포지토리 연결 또는 코드 업로드
3. 새 프로젝트 생성

### 2. 환경 변수 설정
Railway 대시보드에서 다음 환경 변수를 설정하세요:

**필수 환경 변수:**
```
OPENAI_API_KEY=your_openai_api_key_here
```

**선택적 환경 변수:**
```
LOG_LEVEL=INFO
DEBUG_MODE=false
```

### 3. 배포 설정
프로젝트 루트에 포함된 파일들:
- `railway.json`: Railway 배포 설정
- `Procfile`: 프로세스 실행 명령
- `runtime.txt`: Python 버전 지정
- `requirements.txt`: 필요한 패키지 목록

### 4. 자동 배포
- GitHub에 코드를 푸시하면 자동으로 배포됩니다
- Railway 대시보드에서 배포 진행상황을 확인할 수 있습니다

### 5. 접속 확인
배포 완료 후:
1. Railway에서 제공하는 도메인으로 접속
2. 웹 앱이 정상적으로 로드되는지 확인
3. OpenAI API 키가 올바르게 설정되었는지 테스트

## 📋 배포 체크리스트

- [ ] OpenAI API 키 환경 변수 설정
- [ ] `requirements.txt`에 모든 의존성 포함
- [ ] Railway 프로젝트 생성 및 연결
- [ ] 배포 후 기본 기능 테스트

## 🔧 문제 해결

### 일반적인 배포 오류
1. **패키지 설치 오류**: `requirements.txt` 확인
2. **환경 변수 오류**: Railway 대시보드에서 OPENAI_API_KEY 확인
3. **포트 오류**: Railway가 자동으로 PORT 환경 변수 설정

### 로그 확인
Railway 대시보드의 "Deployments" 탭에서 배포 로그를 확인할 수 있습니다.

## 💡 최적화 팁

1. **비용 절약**: 사용하지 않을 때는 앱을 일시정지
2. **성능**: 이미지 생성은 시간이 오래 걸리므로 사용자에게 안내
3. **모니터링**: Railway 대시보드에서 리소스 사용량 확인

## 🎯 배포 완료!

모든 설정이 완료되면 광고 웹툰 생성기를 웹에서 사용할 수 있습니다.