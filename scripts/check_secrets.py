#@title 업로드 파일 비밀값 검사
#@markdown Git에 올릴 파일에 API 키 형태의 문자열이나 실제 로컬 키가 포함됐는지 검사해요.
from pathlib import Path # 검사 파일 경로 도구
import re # 키 형태 검색 도구
import subprocess # Git 추적 목록 읽기 도구
def main(): # 업로드 전 점검 함수
    files = subprocess.check_output(["git", "ls-files", "-z"]).split(b"\0") # 실제 추적 파일 목록
    leaks = [] # 비밀값 발견 위치
    secret = "" # 비교할 로컬 키 초기값
    local = Path(".env") # 비공개 설정 파일 위치
    if local.exists(): # 로컬 설정이 있는 조건
        for line in local.read_text(encoding="utf-8-sig").splitlines(): # 키 설정 읽기
            if line.startswith("OPENAI_API_KEY="): # API 키 설정 식별 조건
                secret = line.split("=", 1)[1].strip() # 출력하지 않을 실제 키
    for raw in files: # 업로드 파일 반복
        if not raw: # 마지막 빈 항목 조건
            continue # 빈 항목 제외
        path = Path(raw.decode("utf-8")) # 파일 경로 복원
        data = path.read_bytes() # 파일 바이트 읽기
        if re.search(rb"sk-[A-Za-z0-9_-]{20,}", data) or (secret and secret.encode() in data): # 키 형태와 실제 키 검사
            leaks.append(str(path)) # 비밀값 자체 대신 파일 위치만 기록
    if any(raw.decode("utf-8").replace("\\", "/").split("/")[-1] == ".env" for raw in files if raw): # 설정 파일 추적 여부 검사
        leaks.append(".env가 Git 추적 목록에 있어요.") # 설정 파일 업로드 방지
    if leaks: # 비밀값이 발견된 조건
        raise SystemExit("업로드 중단: " + ", ".join(leaks)) # 비밀값 노출 없는 실패 안내
    print(f"비밀값 검사 통과: 추적 파일 {sum(bool(raw) for raw in files)}개") # 점검 완료 안내
if __name__ == "__main__": # 직접 실행 조건
    main() # 비밀값 점검 실행
