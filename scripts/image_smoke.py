#@title 선택 사진 입력 기능 확인
#@markdown 직접 그린 테스트 그림으로 사진 전처리와 실제 OpenAI 이미지 입력 경로를 한 번 확인해요.
import json # 기능 점검 결과 저장 도구
from pathlib import Path # 예제 경로 도구
from PIL import Image, ImageDraw # 외부 저작물이 없는 테스트 그림 도구
from gage_hanjul.models import Brief # 입력 규격
from gage_hanjul.service import generate # 실제 생성 파이프라인
def main(): # 사진 기능 점검 함수
    path = Path("examples/product-test.png") # 합성 테스트 그림 경로
    picture = Image.new("RGB", (640, 640), "#f0e7db") # 테스트 배경
    draw = ImageDraw.Draw(picture) # 도형 그리기 도구
    draw.rounded_rectangle((205, 180, 435, 540), radius=35, fill="#f2b5c1", outline="#ffffff", width=12) # 분홍 음료 컵 그림
    draw.ellipse((200, 145, 440, 225), fill="#fff7f3", outline="#ffffff", width=10) # 컵의 위쪽 그림
    draw.line((370, 85, 350, 325), fill="#377b60", width=18) # 초록 빨대 그림
    draw.ellipse((130, 450, 225, 545), fill="#d45264") # 빨간 장식 도형
    picture.save(path) # 테스트 그림 저장
    brief = Brief.model_validate_json(Path("examples/cafe.json").read_text(encoding="utf-8")) # 공개 가상 상품 정보
    result = generate(brief, image=path.read_bytes()) # 최종 방식의 사진 입력 기능 호출
    target = Path("verification/image_smoke.json") # 기능 점검 결과 경로
    target.parent.mkdir(exist_ok=True) # 저장 폴더 생성
    target.write_text(json.dumps({"fixture": "직접 그린 합성 음료 그림이며 실제 상품 사진이 아님", "result": result}, ensure_ascii=False, indent=2), encoding="utf-8") # 실제 점검 결과 저장
    print(json.dumps({"ready": result["ready"], "image_notes": result["bundle"]["image_notes"], "calls": len(result["calls"]), "estimated_usd": sum(call["estimated_usd"] for call in result["calls"])}, ensure_ascii=False)) # 이미지 경로 확인 결과
if __name__ == "__main__": # 직접 실행 조건
    main() # 한 번의 사진 기능 점검 실행
