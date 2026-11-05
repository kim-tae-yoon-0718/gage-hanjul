#@title 실제 API 비교 평가 실행
#@markdown 고정 평가셋을 두 번 반복하고 응답·채점·토큰·실제 수행 시각을 결과 파일에 기록해요.
import argparse # 실행 옵션 도구
from concurrent.futures import ThreadPoolExecutor # 서로 독립된 평가 요청을 병렬 실행하는 도구
from datetime import datetime, timezone # 실제 실행 시각을 기록하는 도구
import hashlib # 입력과 코드의 고정 여부를 확인하는 도구
import json # 평가 자료와 결과 저장 도구
from pathlib import Path # 파일 경로 도구
import subprocess # 실행 버전 확인 도구
from gage_hanjul.models import Brief # 입력 검증 도구
from gage_hanjul.service import generate # 광고 생성 도구
from gage_hanjul.provider import GenerationError # API 오류 유형
from gage_hanjul.evaluation import score, summarize # 공통 평가 도구
def main(): # 실험 실행 함수
    parser = argparse.ArgumentParser() # 옵션 해석 도구
    parser.add_argument("--stage", choices=["baseline", "evidence"], default="baseline") # 평가 버전 옵션
    parser.add_argument("--repeat", type=int, default=2, choices=[1, 2]) # 반복 수 제한
    parser.add_argument("--limit", type=int, default=18) # 실행 건수 옵션
    parser.add_argument("--out", default="experiments/baseline") # 결과 폴더 옵션
    args = parser.parse_args() # 옵션 읽기
    dataset = Path("data/evalset_v1.jsonl") # 고정 평가셋 경로
    cases = [json.loads(line) for line in dataset.read_text(encoding="utf-8").splitlines()][:max(1, min(args.limit, 18))] # 최대 18건 입력
    output = Path(args.out) # 실험 저장 위치
    output.mkdir(parents=True, exist_ok=True) # 저장 폴더 생성
    if (output / "responses.jsonl").exists(): # 기존 결과 덮어쓰기 방지 조건
        parser.error("기존 실험 결과가 있어요. 새 출력 폴더를 지정해주세요.") # 재현 기록 보호
    tracked = [dataset, Path("src/gage_hanjul/evaluation.py"), Path("src/gage_hanjul/validation.py"), *sorted(Path("prompts").glob("*.txt"))] # 해시를 고정할 파일 목록
    manifest = {"stage": args.stage, "repeat": args.repeat, "started_at": datetime.now(timezone.utc).isoformat(), "git_commit": subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip(), "hashes": {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in tracked}, "max_calls": len(cases) * args.repeat, "cost_note": "gpt-5-mini 표준 텍스트 요율, 캐시 할인 미반영. 사진 평가 없음."} # 실험 조건 기록
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8") # 실행 전 조건 저장
    def run(job): # 한 사례를 실행하는 함수
        case, repeat = job # 사례와 반복 번호
        row = {"id": case["id"], "repeat": repeat, "stage": args.stage, "actual_at": datetime.now(timezone.utc).isoformat()} # 실제 실행 정보
        try: # 개별 호출 실패 처리 영역
            result = generate(Brief.model_validate(case["brief"]), args.stage) # 실제 모델 호출
            row.update({"status": "ok", "result": result, "score": score(result, case), "calls": result["calls"]}) # 정상 응답 기록
        except (GenerationError, ValueError) as error: # 실패를 정상 결과로 숨기지 않는 처리
            row.update({"status": "error", "error": str(error), "calls": []}) # 실패 상태 저장
        return row # 한 문항의 기록 반환
    jobs = [(case, repeat) for repeat in range(1, args.repeat + 1) for case in cases] # 고정된 작업 순서
    records = [] # 실험 결과 목록
    with ThreadPoolExecutor(max_workers=3) as pool: # 독립 요청 세 개씩 실행하는 도구
        for row in pool.map(run, jobs): # 결과를 입력 순서대로 수집하는 반복
            records.append(row) # 결과 누적
            with (output / "responses.jsonl").open("a", encoding="utf-8") as stream: # 중간 결과를 보존하는 도구
                stream.write(json.dumps(row, ensure_ascii=False) + "\n") # 응답과 점수를 한 줄로 저장
            print(f"{args.stage} {len(records)}/{len(jobs)} {row['id']} {row['status']}", flush=True) # 비밀값 없는 진행 안내
    summary = summarize(records) # 최종 통계 계산
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8") # 요약 결과 저장
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True) # 실험 결과 표시
if __name__ == "__main__": # 직접 실행 조건
    main() # 실험 실행
