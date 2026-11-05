#@title 광고 생성 기본 파이프라인
#@markdown 확인한 상품 정보로 광고 세 가지를 만들고 자동 점검 결과를 붙여요.
import base64 # 사진을 API 입력으로 바꾸는 도구
import io # 사진을 메모리에서 처리하는 도구
from pathlib import Path # 프롬프트 파일을 읽는 도구
from PIL import Image, ImageOps # 사진 방향과 크기를 처리하는 도구
from .models import Brief, CHANNELS # 입력 규격과 채널 기준
from .provider import call_openai, GenerationError # API 연결 도구
from .validation import validate # 광고 점검 도구
ROOT = Path(__file__).resolve().parents[2] # 프로젝트 기본 경로
def prepare_image(data: bytes) -> str: # 업로드 사진을 준비하는 함수
    if len(data) > 5 * 1024 * 1024: # 파일 크기 제한 조건
        raise GenerationError("사진은 5MB 이하로 올려주세요.") # 파일 크기 안내
    try: # 이미지 파일 오류 처리 영역
        with Image.open(io.BytesIO(data)) as original: # 사진 파일을 메모리로 여는 도구
            if original.format not in {"JPEG", "PNG", "WEBP"} or original.width * original.height > 20_000_000: # 허용 형식과 픽셀 수를 검사하는 조건
                raise ValueError("unsupported image") # 지원하지 않는 사진을 차단하는 오류
            image = ImageOps.exif_transpose(original).convert("RGB") # 촬영 방향을 보정하고 색상을 통일하는 도구
            image.thumbnail((1024, 1024)) # 크기를 줄여 전송량을 낮추는 도구
            buffer = io.BytesIO() # 압축 사진을 담는 메모리 상자
            image.save(buffer, format="JPEG", quality=82) # 메타데이터 없이 JPEG로 저장하는 도구
    except (OSError, ValueError, Image.DecompressionBombError): # 손상된 사진과 과도한 사진 처리
        raise GenerationError("PNG·JPG·WEBP 상품 사진을 확인해주세요.") from None # 사진 수정 안내
    return "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode() # API에 전달할 사진 문자열
def generate(brief: Brief, stage: str = "baseline", image: bytes | None = None, api_key: str | None = None) -> dict: # 광고 세 가지를 만드는 함수
    if stage != "baseline": # 아직 구현하지 않은 실험을 막는 조건
        raise ValueError("지원하는 버전은 baseline이에요.") # 잘못된 버전 안내
    instructions = (ROOT / "prompts" / "baseline.txt").read_text(encoding="utf-8") # 기본 프롬프트
    payload = {"brief": brief.model_dump(), "channel_limits": CHANNELS[brief.channel]} # 상품 정보와 글자 수 기준
    bundle, meta = call_openai(instructions, payload, prepare_image(image) if image else None, api_key) # 광고 생성 요청
    issues = validate(bundle, brief) # 결과를 자동 점검하는 도구
    return {"stage": stage, "brief": brief.model_dump(), "bundle": bundle.model_dump(), "issues": issues, "ready": not issues, "calls": [meta]} # 광고와 점검 내역을 반환하는 도구
def to_markdown(result: dict) -> str: # 내려받을 문서를 만드는 함수
    lines = ["# 가게한줄 광고 문구", "", f"자동 점검: {'통과' if result['ready'] else '수정 필요'}", "", "자동 점검은 의미 전체나 광고 적법성을 보증하지 않습니다. 게시 전 직접 확인해주세요."] # 문서 머리말
    for index, item in enumerate(result["bundle"]["variants"], 1): # 광고안을 하나씩 문서로 바꾸는 반복
        lines.extend(["", f"## 광고안 {index}", item["headline"], "", item["body"], "", item["cta"], " ".join(item["hashtags"])]) # 복사할 문구를 담는 도구
    lines.extend(["", "## 확인 사항", *result["bundle"]["warnings"], *[issue["detail"] for issue in result["issues"]]]) # 추가 확인 사항
    return "\n".join(lines) # 다운로드 문서를 완성하는 도구
