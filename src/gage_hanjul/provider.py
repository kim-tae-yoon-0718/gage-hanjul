#@title OpenAI 광고 생성 연결
#@markdown 공식 Responses API로만 요청하고 키와 원본 응답 오류는 로그에 남기지 않아요.
import json # 요청과 응답을 변환하는 도구
import os # 실행 환경에서 키를 읽는 도구
import time # 응답 시간을 측정하는 도구
from pathlib import Path # 설정 파일 위치를 다루는 도구
from urllib.error import HTTPError, URLError # 연결 오류를 구분하는 도구
from urllib.request import Request, urlopen # HTTPS 요청 도구
from .models import AdBundle # 구조화 출력 규격
class GenerationError(RuntimeError): # 사용자에게 보여줄 연결 오류
    pass # 기본 예외 동작을 그대로 쓰는 설정
def load_env(path: str = ".env") -> None: # 로컬 설정 파일을 읽는 함수
    file = Path(path) # 설정 파일 경로
    if file.exists(): # 파일이 있을 때만 읽는 조건
        for line in file.read_text(encoding="utf-8-sig").splitlines(): # 설정을 한 줄씩 읽는 반복
            if "=" in line and not line.lstrip().startswith("#"): # 실제 설정 줄을 구분하는 조건
                key, value = line.split("=", 1) # 이름과 값을 나누는 도구
                os.environ.setdefault(key.strip(), value.strip().strip("\"'")) # 기존 환경변수 우선으로 설정하는 도구
def call_openai(instructions: str, payload: dict, image_url: str | None = None, api_key: str | None = None) -> tuple[AdBundle, dict]: # 광고 생성 요청 함수
    load_env() # 로컬 환경 설정을 읽는 도구
    secret = api_key or os.getenv("OPENAI_API_KEY", "") # 사용자 키를 읽는 도구
    if not secret.strip(): # 키 누락 조건
        raise GenerationError("OpenAI API 키를 입력하거나 .env에 설정해주세요.") # 설정 방법을 안내하는 오류
    content = [{"type": "input_text", "text": json.dumps(payload, ensure_ascii=False)}] # 사용자 상품 정보
    if image_url: # 사진이 있을 때의 조건
        content.append({"type": "input_image", "image_url": image_url, "detail": "low"}) # 저해상도로 사진을 함께 전달하는 도구
    request_data = {"model": os.getenv("OPENAI_MODEL", "gpt-5-mini"), "instructions": instructions, "input": [{"role": "user", "content": content}], "reasoning": {"effort": "minimal"}, "text": {"format": {"type": "json_schema", "name": "advertisement", "strict": True, "schema": AdBundle.model_json_schema()}}, "max_output_tokens": 2200, "store": False} # 구조화 응답과 비용 상한을 정하는 설정
    request = Request("https://api.openai.com/v1/responses", data=json.dumps(request_data).encode(), headers={"Authorization": f"Bearer {secret.strip()}", "Content-Type": "application/json"}, method="POST") # 공식 API 요청
    started = time.perf_counter() # 요청 시작 시각
    try: # 네트워크 오류를 처리하는 영역
        with urlopen(request, timeout=100) as response: # 재시도 없이 한 번만 호출하는 도구
            result = json.load(response) # 응답 JSON을 읽는 도구
    except HTTPError as error: # HTTP 오류를 구분하는 처리
        messages = {401: "API 키 인증에 실패했어요.", 403: "이 키로 선택 모델에 접근할 수 없어요.", 429: "사용량 한도 또는 요청 제한에 걸렸어요. 잠시 후 한도를 확인해주세요."} # 사용자 안내 문구
        raise GenerationError(messages.get(error.code, f"OpenAI 연결 오류({error.code})가 발생했어요.")) from None # 비밀값 없는 오류
    except (URLError, TimeoutError, OSError): # 네트워크와 시간 초과 처리
        raise GenerationError("네트워크 연결 또는 응답 시간을 확인해주세요.") from None # 연결 안내
    usage = result.get("usage", {}) # 실제 토큰 사용량
    input_tokens, output_tokens = usage.get("input_tokens", 0), usage.get("output_tokens", 0) # 입력과 출력 토큰 수
    meta = {"response_id": result.get("id"), "model": result.get("model"), "input_tokens": input_tokens, "output_tokens": output_tokens, "seconds": round(time.perf_counter() - started, 3), "estimated_usd": round((input_tokens * 0.25 + output_tokens * 2.0) / 1_000_000, 8)} # 캐시 할인을 제외한 보수적 비용 기록
    if result.get("status") != "completed": # 잘린 응답을 찾는 조건
        raise GenerationError("응답이 완성되지 않았어요. 입력을 줄인 뒤 다시 시도해주세요.") # 불완전 출력을 막는 오류
    pieces = [part.get("text", "") for item in result.get("output", []) for part in item.get("content", []) if part.get("type") == "output_text"] # 설명 배열에서 광고 텍스트만 모으는 도구
    try: # 구조화 출력 파싱 영역
        bundle = AdBundle.model_validate_json("".join(pieces)) # 출력 규격을 검사하는 도구
    except ValueError: # 거절 또는 잘못된 출력 처리
        raise GenerationError("광고 응답을 만들지 못했어요. 상품 정보와 요청을 확인해주세요.") from None # 사용자 안내
    return bundle, meta # 광고와 사용량을 함께 반환하는 도구
