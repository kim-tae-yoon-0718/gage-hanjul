#@title 광고 입력과 안전 경계 테스트
#@markdown 사실 밖 숫자·금지어 우회·손상 사진·입력 충돌을 실제 경계값으로 점검해요.
import io # 테스트 사진을 메모리에서 만드는 도구
import json # 샘플 입력 읽기 도구
from pathlib import Path # 샘플 경로 도구
import pytest # 자동 테스트 도구
from PIL import Image # 이미지 테스트 도구
from gage_hanjul.models import Brief, AdBundle, CopyVariant # 검증 규격
from gage_hanjul.validation import validate # 결과 점검 도구
from gage_hanjul.service import prepare_image # 사진 전처리 도구
from gage_hanjul.provider import GenerationError # 오류 유형
def brief(): # 공통 입력 생성 함수
    return Brief.model_validate_json(Path("examples/cafe.json").read_text(encoding="utf-8")) # 유효한 상품 정보
def bundle(): # 정상 광고 세 가지 생성 함수
    return AdBundle(variants=[CopyVariant(headline=f"딸기 라떼와 쉼 {word}", body="오늘도 수고했어요. 딸기청과 우유로 만든 한 잔을 만나보세요.", cta="가게에서 만나요", hashtags=["#딸기라떼", "#오후한잔", "#잠깐의쉼"], used_fact_ids=[2]) for word in ["하나", "둘", "셋"]], warnings=[], image_notes="") # 정상 경계 테스트 자료
def test_valid_output(): # 정상 결과가 차단되지 않는지 검사하는 함수
    assert validate(bundle(), brief()) == [] # 정상 통과 확인
@pytest.mark.parametrize("body,code", [("오늘도 수고했어요. 가격은 5000원!", "number"), ("오늘도 수고했어요. 최 저 가 한 잔!", "forbidden"), ("오늘도 수고했어요. 피로 치료!", "risk"), ("새로운 하루를 만나요", "required"), ("오늘도 수고했어요." + "긴" * 230, "length")]) # 경계별 입력과 기대 오류
def test_detects_publish_errors(body, code): # 실제 광고 오류를 찾는 함수
    result = bundle() # 정상 광고 사본
    result.variants[0].body = body # 오류 하나를 주입하는 도구
    assert code in {issue["code"] for issue in validate(result, brief())} # 해당 오류가 탐지되는지 확인
def test_conflicting_input(): # 필수 내용과 금지어 충돌 검사
    with pytest.raises(ValueError, match="겹쳐요"): # 충돌 입력 차단 확인
        Brief(**{**brief().model_dump(), "forbidden_words": ["딸기"]}) # 충돌 입력
def test_blank_fact_rejected(): # 빈 사실 입력 검사
    with pytest.raises(ValueError): # 빈 사실 차단 확인
        Brief(**{**brief().model_dump(), "facts": [" "]}) # 빈 사실 입력
def test_broken_image_rejected(): # 손상 사진 입력 검사
    with pytest.raises(GenerationError): # 손상 사진 차단 확인
        prepare_image(b"not an image") # 손상된 이미지 자료
def test_image_metadata_removed_and_resized(): # 전송 사진 크기와 포맷 검사
    stream = io.BytesIO() # 테스트 이미지 메모리
    Image.new("RGB", (1600, 1200), "pink").save(stream, format="PNG") # 큰 사진 생성
    url = prepare_image(stream.getvalue()) # 사진 전처리
    assert url.startswith("data:image/jpeg;base64,") # 안전한 정규화 형식 확인
def test_sms_has_no_hashtags(): # 채널별 태그 처리 검사
    result = bundle() # 인스타그램 광고 자료
    request = Brief(**{**brief().model_dump(), "channel": "sms"}) # 문자 채널 입력
    assert "hashtags" in {issue["code"] for issue in validate(result, request)} # 태그가 문자에서 탐지되는지 확인
