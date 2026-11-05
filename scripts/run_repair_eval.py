#@title 두 번째 개선 실험 실행
#@markdown 실험 1의 같은 초안을 재사용하고 자동 점검 실패에만 최대 한 번 수정 요청을 보내요.
import argparse # 옵션 해석 도구
from concurrent.futures import ThreadPoolExecutor # 독립 수정 요청 병렬 실행 도구
from datetime import datetime, timezone # 실제 실행 시각 기록 도구
import hashlib # 자료와 코드 버전 확인 도구
import json # 결과 파일 입출력 도구
from pathlib import Path # 파일 경로 도구
import subprocess # Git 버전 기록 도구
from gage_hanjul.service import repair_result # 조건부 단일 수정 도구
from gage_hanjul.evaluation import score, summarize # 같은 채점 기준 도구
def main(): # 두 번째 개선 실험 진입 함수
    parser = argparse.ArgumentParser() # 실행 옵션 상자
    parser.add_argument("--source", default="experiments/evidence/responses.jsonl") # 재사용할 초안 경로
    parser.add_argument("--out", default="experiments/repair") # 결과 저장 위치
    args = parser.parse_args() # 옵션 읽기
    source = Path(args.source) # 초안 파일 위치
    rows = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines()] # 실제 초안 원본
    if len(rows) > 36 or any(row["status"] != "ok" or row["stage"] != "evidence" for row in rows): # 정식 실험 입력 범위 확인
        parser.error("정상 완료된 실험 1 결과 36개 이하만 사용할 수 있어요.") # 다른 초안 혼입 차단
    output = Path(args.out) # 출력 경로
    output.mkdir(parents=True, exist_ok=True) # 결과 폴더 생성
    if (output / "responses.jsonl").exists(): # 기존 기록 보호 조건
        parser.error("결과가 이미 있어요. 새 폴더를 지정해주세요.") # 덮어쓰기 차단
    cases = {case["id"]: case for case in (json.loads(line) for line in Path("data/evalset_v1.jsonl").read_text(encoding="utf-8").splitlines())} # 고정 평가 사례
    paths = [Path("data/evalset_v1.jsonl"), *Path("src/gage_hanjul").glob("*.py"), *Path("prompts").glob("*.txt"), source] # 재현에 필요한 자료
    manifest = {"stage": "repair", "started_at": datetime.now(timezone.utc).isoformat(), "git_commit": subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip(), "hashes": {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}, "source": str(source), "design": "실험 1의 동일 초안을 재사용. 통과 초안은 그대로, 실패 초안은 최대 한 번 수정. 정답 표지는 수정 프롬프트에 전달하지 않음."} # 실험 조건
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8") # 실행 전 조건 기록
    def run(row): # 초안 한 개 수정 함수
        result = repair_result(row["result"]) # 같은 초안과 공통 검증기만 사용
        return {"id": row["id"], "repeat": row["repeat"], "stage": "repair", "status": "ok", "source_response_id": row["calls"][0]["response_id"], "actual_at": datetime.now(timezone.utc).isoformat(), "result": result, "score": score(result, cases[row["id"]]), "calls": result["calls"], "new_call_count": len(result["calls"]) - len(row["calls"])} # 전후 비교와 신규 호출 구분
    records = [] # 수정 결과 목록
    with ThreadPoolExecutor(max_workers=3) as pool: # 독립 수정 요청 세 개씩 실행
        for result in pool.map(run, rows): # 고정된 순서로 결과 수집
            records.append(result) # 결과 누적
            with (output / "responses.jsonl").open("a", encoding="utf-8") as stream: # 중간 결과 보존
                stream.write(json.dumps(result, ensure_ascii=False) + "\n") # 수정 결과 저장
            print(f"repair {len(records)}/{len(rows)} {result['id']} new_calls={result['new_call_count']}", flush=True) # 실제 추가 호출 안내
    summary = summarize(records) # 같은 기준으로 통계 계산
    summary["new_calls"] = sum(row["new_call_count"] for row in records) # 새로 실행한 API 호출 수
    summary["new_estimated_usd"] = round(sum(call["estimated_usd"] for row in records for call in row["calls"][1:]), 6) # 재사용 비용을 빼고 신규 비용만 계산
    summary["repair_errors"] = sum("repair_error" in row["result"] for row in records) # 실패한 수정 요청 개수
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8") # 요약 저장
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True) # 실험 결과 출력
if __name__ == "__main__": # 직접 실행 조건
    main() # 두 번째 개선 실험 실행
