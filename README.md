# 가게한줄

> 확인한 상품 정보로 우리 가게의 광고 문구 세 가지를 만드는 로컬 서비스입니다.

인스타그램, 문자 초안, 배너 문구를 생성하고 글자 수·필수 문구·금지어·숫자를 점검합니다. 상품 사진은 선택 사항입니다. OpenAI API만 사용하며 GPU와 Hugging Face 모델은 필요하지 않습니다.

## 빠른 시작

Python 3.10 이상을 준비한 뒤 저장소 루트에서 실행하세요.

```powershell
#@title 실행 환경 준비
#@markdown 가상환경을 만들고 프로젝트와 검증 도구를 설치해요.
python -m venv .venv # 독립 실행 환경을 만드는 도구
.\.venv\Scripts\python.exe -m pip install -e ".[dev]" # 실행 및 검증 패키지 설치
Copy-Item .env.example .env # 키 설정 파일을 준비하는 도구
```

`.env`의 OPENAI_API_KEY에 본인 키를 넣으세요. .env는 GitHub에 올라가지 않습니다.

```powershell
#@title 광고 제작 화면 실행
#@markdown 브라우저에서 상품 정보를 입력하고 문구를 내려받을 수 있어요.
.\.venv\Scripts\python.exe -m streamlit run app.py # 로컬 제작 화면을 여는 도구
```

현재 기본 버전 구현과 정식 평가를 진행하고 있습니다. 최종 실험 결과·보고서·업무일지는 검증 후 이 문서에 연결합니다.
