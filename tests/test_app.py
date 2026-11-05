#@title 실제 광고 화면 테스트
#@markdown 앱 초기 화면과 입력 폼이 오류 없이 표시되는지 확인해요.
from streamlit.testing.v1 import AppTest # Streamlit의 실제 화면 검증 도구
from pathlib import Path # 앱의 절대 경로를 찾는 도구
def test_app_loads_without_api_call(): # 유료 호출 없는 앱 실행 검사
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py").run(timeout=20) # 실제 앱 실행
    assert not app.exception # 화면 오류가 없는지 확인
    assert app.title[0].value == "우리 가게의 매력을, 한 줄 더." # 주요 화면 표시 확인
    assert len(app.button) >= 1 # 생성 버튼 표시 확인
