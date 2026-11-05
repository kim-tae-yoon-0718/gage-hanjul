#@title 터미널 광고 생성 실행
#@markdown 상품 JSON을 읽어 광고 Markdown과 점검 JSON을 저장해요.
import argparse # 실행 옵션을 읽는 도구
import json # 상품 정보와 결과를 읽고 쓰는 도구
from pathlib import Path # 입출력 파일을 다루는 도구
from .models import Brief # 상품 입력 검증 도구
from .provider import GenerationError # 사용자 안내 오류
from .service import generate, to_markdown # 광고 생성과 문서 변환 도구
def main(): # 터미널 진입 함수
    parser = argparse.ArgumentParser(description="가게한줄 광고 문구 생성") # 명령 설명 도구
    parser.add_argument("--brief", default="examples/cafe.json") # 입력 파일 옵션
    parser.add_argument("--stage", default="repair", choices=["baseline", "evidence", "repair"]) # 생성 버전 옵션
    parser.add_argument("--image") # 선택 사진 옵션
    parser.add_argument("--out", default=".local/ad") # 저장 위치 옵션
    args = parser.parse_args() # 실행 옵션을 읽는 도구
    try: # 입력과 API 오류 처리 영역
        brief = Brief.model_validate_json(Path(args.brief).read_text(encoding="utf-8")) # 상품 정보를 검증하는 도구
        result = generate(brief, args.stage, Path(args.image).read_bytes() if args.image else None) # 광고 생성
        target = Path(args.out) # 저장 파일의 기본 경로
        target.parent.mkdir(parents=True, exist_ok=True) # 출력 폴더를 만드는 도구
        target.with_suffix(".json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8") # 점검 가능한 JSON 저장
        target.with_suffix(".md").write_text(to_markdown(result), encoding="utf-8") # 사용하기 쉬운 문서 저장
        print(f"저장했어요: {target}.md / 자동 점검 {'통과' if result['ready'] else '수정 필요'}") # 실행 결과 안내
    except (ValueError, OSError, GenerationError) as error: # 입력과 생성 실패 처리
        parser.exit(1, f"실행하지 못했어요: {error}\n") # 실패 상태로 종료하는 도구
if __name__ == "__main__": # 직접 실행했을 때의 조건
    main() # 광고 생성 실행
