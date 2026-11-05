#@title 광고 입력과 출력 규격
#@markdown 입력 오류를 미리 찾고 광고 세 가지를 같은 형태로 받아요.
from typing import Literal # 허용된 선택값을 정의하는 도구
from pydantic import BaseModel, ConfigDict, Field, model_validator # 데이터 검증 도구
CHANNELS = {"instagram": {"label": "인스타그램", "headline": 30, "body": 220, "cta": 30, "tags": 3}, "sms": {"label": "문자", "headline": 20, "body": 90, "cta": 20, "tags": 0}, "banner": {"label": "배너", "headline": 16, "body": 45, "cta": 12, "tags": 0}} # 서비스 내부 글자 수 기준
class Brief(BaseModel): # 사용자가 제공한 상품 정보를 담는 상자
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True) # 잘못된 필드와 앞뒤 공백을 처리하는 설정
    store: str = Field(min_length=1, max_length=40) # 가게 이름
    product: str = Field(min_length=1, max_length=40) # 상품 이름
    audience: str = Field(min_length=1, max_length=100) # 광고 대상
    tone: Literal["다정한", "담백한", "활기찬"] = "다정한" # 문구 분위기
    channel: Literal["instagram", "sms", "banner"] = "instagram" # 게시 채널
    facts: list[str] = Field(min_length=1, max_length=8) # 사용자가 확인한 사실 목록
    required_phrase: str = Field(default="", max_length=30) # 반드시 넣을 문구
    forbidden_words: list[str] = Field(default_factory=list, max_length=10) # 피할 표현 목록
    request: str = Field(default="", max_length=400) # 창작 방향 요청
    @model_validator(mode="after") # 필드 사이의 충돌을 검사하는 도구
    def check_brief(self): # 광고 생성 전에 입력을 점검하는 함수
        if any(not fact.strip() or len(fact) > 160 for fact in self.facts): # 빈 사실이나 너무 긴 사실을 찾는 조건
            raise ValueError("확인한 사실은 각각 1~160자로 적어주세요.") # 수정할 입력을 안내하는 오류
        if any(not word.strip() or len(word) > 30 for word in self.forbidden_words): # 금지어 길이를 검사하는 조건
            raise ValueError("금지어는 각각 1~30자로 적어주세요.") # 금지어 수정 안내
        compact = lambda value: "".join(value.split()).casefold() # 공백과 대소문자 차이를 없애는 도구
        mandatory = [self.store, self.product, self.required_phrase] # 필수값을 담는 목록 #[1 가게, 2 상품, 3 필수 문구]
        if any(compact(word) in compact(value) for word in self.forbidden_words for value in mandatory if value): # 필수값과 금지어가 겹치는지 확인하는 조건
            raise ValueError("가게·상품·필수 문구와 금지어가 겹쳐요.") # 해결할 수 없는 요청을 막는 오류
        if len(self.product) + len(self.required_phrase) > sum(CHANNELS[self.channel][key] for key in ("headline", "body", "cta")): # 좁은 채널에 필수 내용이 들어가는지 검사하는 조건
            raise ValueError("선택한 채널에 비해 필수 내용이 너무 길어요.") # 채널 변경 안내
        return self # 검사한 입력을 반환하는 도구
class CopyVariant(BaseModel): # 한 개의 광고안을 담는 상자
    model_config = ConfigDict(extra="forbid") # 정의하지 않은 출력 필드를 막는 설정
    headline: str # 광고 제목
    body: str # 광고 본문
    cta: str # 행동 유도 문구
    hashtags: list[str] # 해시태그 목록
    used_fact_ids: list[int] # 사용한 사실의 번호 목록
class AdBundle(BaseModel): # 광고 세 가지와 안내를 담는 상자
    model_config = ConfigDict(extra="forbid") # 출력 필드 오타를 막는 설정
    variants: list[CopyVariant] # 광고안 목록
    warnings: list[str] # 사용자 확인 사항
    image_notes: str # 사진에서 참고한 외형 설명
