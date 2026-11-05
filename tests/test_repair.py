#@title 단일 수정과 호출 절약 검증
#@markdown 통과 광고는 재호출하지 않고 실패 광고도 한 번만 수정하는지 확인해요.
from unittest.mock import patch # API 호출을 대신하는 검증 도구
from gage_hanjul.service import repair_result # 실제 수정 파이프라인
from gage_hanjul.validation import validate # 같은 검증 기준
from test_contract import brief, bundle # 정상 경계 자료
def draft(): # 초안 생성 함수
    item = bundle() # 정상 광고 세 가지
    return {"stage": "evidence", "brief": brief().model_dump(), "bundle": item.model_dump(), "issues": [], "ready": True, "calls": [{"estimated_usd": 0.001, "seconds": 1}]} # 호출 기록이 있는 초안
def test_passed_draft_does_not_call_model(): # 통과 초안의 추가 호출 방지 검사
    original = draft() # 재사용할 초안
    with patch("gage_hanjul.service.call_openai") as model: # 유료 호출 차단
        result = repair_result(original) # 수정 경로 실행
    model.assert_not_called() # 실제 호출이 없었는지 확인
    assert result["bundle"] == original["bundle"] # 통과 문구가 바뀌지 않았는지 확인
def test_failed_draft_repairs_once_and_rechecks(): # 단일 수정 한도 검사
    original = draft() # 정상 초안
    original["bundle"]["variants"][0]["body"] = "확인 안 된 5000원" # 수정이 필요한 오류
    with patch("gage_hanjul.service.call_openai", return_value=(bundle(), {"estimated_usd": 0.002, "seconds": 2})) as model: # 수정 응답 대체
        result = repair_result(original) # 수정 경로 실행
    model.assert_called_once() # 한 번만 수정했는지 확인
    assert result["ready"] and len(result["calls"]) == 2 # 수정 후 검사 및 호출 기록 확인
def test_unsolved_error_is_not_marked_ready(): # 수정 실패 결과 처리 검사
    original = draft() # 정상 초안
    original["bundle"]["variants"][0]["body"] = "확인 안 된 5000원" # 오류 주입
    bad = bundle() # 수정 응답 준비
    bad.variants[0].body = "다른 미확인 6000원" # 수정 후에도 남은 오류
    with patch("gage_hanjul.service.call_openai", return_value=(bad, {"estimated_usd": 0.002, "seconds": 2})) as model: # 실패 수정 응답
        result = repair_result(original) # 수정 경로 실행
    model.assert_called_once() # 무한 재시도 방지 확인
    assert not result["ready"] and result["issues"] # 실패를 통과로 숨기지 않았는지 확인
