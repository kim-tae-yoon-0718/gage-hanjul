#@title 비교 실험 결과 분석
#@markdown 세 버전의 채널별 통과율·반복 일치율·실제 신규 비용을 비교 파일로 저장해요.
from collections import defaultdict # 채널별 결과를 모으는 도구
import hashlib # 고정 파일을 확인하는 도구
import json # 실험 결과 읽기와 저장 도구
from pathlib import Path # 결과 경로 도구
from gage_hanjul.evaluation import summarize # 고정 요약 계산 도구
def main(): # 결과 분석 진입 함수
    report = {} # 세 버전 비교 상자
    unique_calls = {} # 재사용 호출을 중복 청구하지 않기 위한 상자
    for stage in ("baseline", "evidence", "repair"): # 세 평가 버전 반복
        folder = Path("experiments") / stage # 해당 결과 폴더
        rows = [json.loads(line) for line in (folder / "responses.jsonl").read_text(encoding="utf-8").splitlines()] # 원본 결과
        grouped = defaultdict(list) # 문항별 반복 결과
        for row in rows: # 각 결과 반복
            grouped[row["id"]].append(row.get("score", {}).get("all_pass", False)) # 문항별 통과 여부
            for call in row["calls"]: # 실제 호출 반복
                unique_calls[call["response_id"]] = call # 재사용 호출의 중복 제거
        summary = summarize(rows) # 공통 요약 다시 계산
        summary["repeat_agreement"] = sum(len(set(values)) == 1 for values in grouped.values()) / len(grouped) # 2회 반복 통과 상태의 일치율
        summary["channels"] = {channel: summarize([row for row in rows if row["id"].endswith(channel)]) for channel in ("instagram", "sms", "banner")} # 채널별 같은 판정 집계
        summary["failures"] = [{"id": row["id"], "repeat": row["repeat"], "issues": row.get("score", {}).get("issues", []), "flags": row.get("score", {}).get("semantic_flags", [])} for row in rows if not row.get("score", {}).get("all_pass", False)] # 실패를 숨기지 않는 목록
        report[stage] = summary # 버전별 결과 저장
    report["physical_eval_calls"] = len(unique_calls) # 실제 정식 평가 호출 수
    report["physical_eval_estimated_usd"] = round(sum(call["estimated_usd"] for call in unique_calls.values()), 8) # 실제 정식 평가 추정 비용
    manifests = [{key.replace("\\", "/"): value for key, value in json.loads((Path("experiments") / stage / "manifest.json").read_text(encoding="utf-8"))["hashes"].items()} for stage in ("baseline", "evidence", "repair")] # Windows와 다른 운영체제의 경로 구분 통일
    report["frozen_hashes_equal"] = {key: len({manifest[key] for manifest in manifests}) == 1 for key in ("data/evalset_v1.jsonl", "src/gage_hanjul/evaluation.py", "src/gage_hanjul/validation.py")} # 조건이 바뀌지 않았는지 확인
    Path("experiments/comparison.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8") # 재계산 가능한 비교 결과 저장
    print(json.dumps({key: value for key, value in report.items() if key not in {"baseline", "evidence", "repair"}}, ensure_ascii=False, indent=2)) # 핵심 추적 결과 표시
if __name__ == "__main__": # 직접 실행 조건
    main() # 분석 실행
