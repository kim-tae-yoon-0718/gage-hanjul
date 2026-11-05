#@title 고정 기준 광고 평가
#@markdown 자동 점검과 숨겨진 사실성 표지를 함께 채점하고 실제 비용·지연을 요약해요.
from collections import Counter # 오류 종류를 합산하는 도구
from statistics import mean, median # 요약 통계 도구
from .models import Brief, AdBundle # 평가할 데이터 규격
from .validation import compact, validate # 공통 점검 도구
def score(result: dict, case: dict) -> dict: # 하나의 생성 결과를 평가하는 함수
    brief = Brief.model_validate(case["brief"]) # 평가 입력 검증
    bundle = AdBundle.model_validate(result["bundle"]) # 출력 검증
    issues = validate(bundle, brief) # 세 버전에 같은 자동 점검 적용
    texts = [compact(" ".join([item.headline, item.body, item.cta, *item.hashtags])) for item in bundle.variants] # 실제 게시 문구 전체
    semantic_flags = [{"variant": index, "term": term} for index, text in enumerate(texts, 1) for term in case["prohibited"] if compact(term) in text] # 프롬프트에 전달하지 않은 정답 표지 검사
    codes = {issue["code"] for issue in issues} # 발생한 자동 점검 종류
    return {"contract_pass": not issues, "factual_probe_pass": not semantic_flags, "all_pass": not issues and not semantic_flags, "issues": issues, "semantic_flags": semantic_flags, "length_pass": "length" not in codes, "required_pass": not codes.intersection({"required", "product"}), "safety_pass": not codes.intersection({"forbidden", "risk", "number"}) and not semantic_flags} # 고정 채점 결과
def summarize(records: list[dict]) -> dict: # 한 실험의 결과를 요약하는 함수
    valid = [record for record in records if record.get("status") == "ok"] # 정상 응답 목록
    all_calls = [call for record in records for call in record.get("calls", [])] # 실제 API 호출 목록
    metrics = {key: round(sum(bool(record["score"][key]) for record in valid) / len(records), 4) if records else 0 for key in ("all_pass", "contract_pass", "factual_probe_pass", "length_pass", "required_pass", "safety_pass")} # 실패 응답도 분모에 포함한 통과율
    metrics.update({"n": len(records), "completed": len(valid), "errors": len(records) - len(valid), "calls": len(all_calls), "estimated_usd": round(sum(call["estimated_usd"] for call in all_calls), 6), "input_tokens": sum(call["input_tokens"] for call in all_calls), "output_tokens": sum(call["output_tokens"] for call in all_calls), "median_seconds": round(median([sum(call["seconds"] for call in record["calls"]) for record in valid]), 3) if valid else None, "mean_seconds": round(mean([sum(call["seconds"] for call in record["calls"]) for record in valid]), 3) if valid else None, "issue_counts": dict(Counter(issue["code"] for record in valid for issue in record["score"]["issues"])), "probe_flags": sum(len(record["score"]["semantic_flags"]) for record in valid)}) # 품질·비용·오류 집계
    return metrics # 요약 결과 반환
