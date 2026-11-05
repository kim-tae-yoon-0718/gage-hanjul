#@title 광고 문구 자동 점검
#@markdown 길이·금지어·미확인 숫자·위험 표현을 찾아 사용 전 확인할 수 있어요.
import re # 숫자와 위험 표현을 찾는 도구
from .models import AdBundle, Brief, CHANNELS # 입력과 출력 기준을 불러오는 도구
RISK = re.compile(r"완치|치료|부작용\s*없|100\s*%\s*(효과|보장)|국내\s*1위|무조건\s*효과") # 서비스에서 허용하지 않는 표현 기준
def compact(text: str) -> str: # 공백 차이를 없애는 함수
    return re.sub(r"\s+", "", text).casefold() # 비교하기 쉬운 문자열을 만드는 도구
def numbers(text: str) -> set[str]: # 숫자와 단위를 함께 추출하는 함수
    return set(re.findall(r"\d+(?:\.\d+)?(?:만원|천원|원|%|개|명|시|분|g|kg|ml|일|월)", compact(text).replace(",", ""))) # 단위가 다른 숫자를 구분하는 도구
def validate(bundle: AdBundle, brief: Brief) -> list[dict]: # 광고 전체의 문제를 찾는 함수
    issues = [] # 발견한 문제를 담는 목록
    def add(code, index, detail): # 같은 형태로 문제를 기록하는 도구
        issues.append({"code": code, "variant": index, "detail": detail}) # 문제 종류와 위치를 저장하는 도구
    limits = CHANNELS[brief.channel] # 선택 채널의 글자 수 기준
    allowed_numbers = numbers(" ".join([brief.store, brief.product, *brief.facts, brief.required_phrase])) # 사실 입력에 포함된 숫자 집합
    if len(bundle.variants) != 3: # 광고 세 가지인지 확인하는 조건
        add("variant_count", 0, "광고안은 정확히 3개여야 해요.") # 개수 오류 기록
    seen = set() # 같은 광고를 찾기 위한 집합
    for index, item in enumerate(bundle.variants, 1): # 광고안을 하나씩 확인하는 반복
        text = " ".join([item.headline, item.body, item.cta, *item.hashtags]) # 게시되는 텍스트 전체
        for field in ("headline", "body", "cta"): # 길이를 검사할 필드 반복
            value = getattr(item, field) # 해당 필드 문구
            if not value.strip() or len(value) > limits[field]: # 빈 문구와 길이 초과를 찾는 조건
                add("length", index, f"{field}: {len(value)}자, 허용 1~{limits[field]}자") # 길이 오류 기록
        if len(item.hashtags) != limits["tags"] or any(not re.fullmatch(r"#[\w가-힣]+", tag) for tag in item.hashtags): # 태그 수와 문법을 검사하는 조건
            add("hashtags", index, f"해시태그는 {limits['tags']}개가 필요해요.") # 태그 오류 기록
        if brief.product not in text: # 상품명 누락을 찾는 조건
            add("product", index, "상품명이 빠졌어요.") # 상품명 누락 기록
        if brief.required_phrase and brief.required_phrase not in text: # 필수 문구 누락 조건
            add("required", index, "필수 문구가 빠졌어요.") # 필수 문구 오류 기록
        for word in brief.forbidden_words: # 금지어를 하나씩 확인하는 반복
            if compact(word) in compact(text): # 띄어쓰기 우회를 포함해 금지어를 찾는 조건
                add("forbidden", index, f"금지 표현: {word}") # 금지어 오류 기록
        for value in sorted(numbers(text) - allowed_numbers): # 사실에 없는 숫자를 찾는 반복
            add("number", index, f"확인되지 않은 숫자·단위: {value}") # 숫자 오류 기록
        if RISK.search(text): # 위험 표현을 찾는 조건
            add("risk", index, "효능·순위·보장 표현을 확인해주세요.") # 위험 표현 기록
        if not item.used_fact_ids or any(value < 1 or value > len(brief.facts) for value in item.used_fact_ids): # 근거 번호의 범위를 확인하는 조건
            add("evidence", index, "사용한 사실 번호가 비어 있거나 범위를 벗어났어요.") # 근거 연결 오류 기록
        fingerprint = compact(item.headline + item.body + item.cta) # 광고안 중복을 비교하는 값
        if fingerprint in seen: # 완전 중복 여부 확인 조건
            add("duplicate", index, "같은 광고안이 반복됐어요.") # 중복 오류 기록
        seen.add(fingerprint) # 확인한 광고를 저장하는 도구
    return issues # 발견한 문제 목록을 돌려주는 도구
