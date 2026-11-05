#@title 가게한줄 광고 제작 화면
#@markdown 상품 정보를 입력하면 광고 3개와 점검 결과를 보고 문구를 내려받을 수 있어요.
import json # 예제와 다운로드 결과를 다루는 도구
import time # 사용자 대기 시간을 측정하는 도구
from pathlib import Path # 프로젝트 파일을 읽는 도구
import streamlit as st # 광고 제작 화면 도구
from gage_hanjul.models import Brief, CHANNELS # 상품 정보와 채널 기준
from gage_hanjul.provider import GenerationError, load_env # 키 설정과 연결 오류 도구
from gage_hanjul.service import generate, to_markdown # 생성 및 문서 변환 도구
st.set_page_config(page_title="가게한줄 · 우리 가게의 다음 한 줄", page_icon="✳", layout="wide") # 화면 제목과 배치 설정
load_env() # 로컬 키 설정을 읽는 도구
st.markdown("<style>.stApp{background:#f7f6f1}.block-container{max-width:1160px;padding-top:3rem}h1,h2,h3{letter-spacing:-.04em}div[data-testid=stMetric]{background:white;padding:18px;border-radius:14px}</style>", unsafe_allow_html=True) # 화면 여백과 색상을 정하는 설정
st.caption("GAGE HANJUL / SMALL BUSINESS COPY STUDIO") # 서비스 설명
st.title("우리 가게의 매력을, 한 줄 더.") # 주 제목
st.write("상품의 확인된 정보로 광고 문구 세 가지를 만들어보세요. 인스타그램부터 짧은 배너까지.") # 사용 흐름 안내
with st.sidebar: # 설정 영역
    st.subheader("✳ 가게한줄") # 서비스 이름
    st.write("01 상품 소개 → 02 광고 제작 → 03 확인하고 사용") # 단계 안내
    key = st.text_input("OpenAI API 키", type="password", help=".env에 설정했다면 비워두세요. 이 화면에서는 디스크에 저장하지 않습니다.") # 선택 키 입력창
    demo = st.toggle("예시 결과 둘러보기", value=False) # 비용 없는 예제 보기
    st.caption("사진과 상품 정보는 생성 요청 시 OpenAI로 전달돼요. GPU와 Hugging Face 모델은 사용하지 않아요.") # 데이터 사용 안내
example = json.loads(Path("examples/cafe.json").read_text(encoding="utf-8")) # 기본 입력 예제
left, right = st.columns([1, 1.15], gap="large") # 입력과 결과 영역
with left: # 상품 입력 영역
    st.subheader("01 / 상품을 소개해주세요") # 입력 제목
    with st.form("brief_form"): # 하나의 입력 묶음
        store = st.text_input("가게 이름", example["store"], max_chars=40) # 가게 이름 입력
        product = st.text_input("상품·서비스 이름", example["product"], max_chars=40) # 상품 이름 입력
        facts = st.text_area("확인한 사실 · 한 줄에 하나", "\n".join(example["facts"]), help="가격, 구성, 포장 여부 등 직접 확인한 정보만 적어주세요.") # 사실 입력
        audience = st.text_input("누구에게 보여줄까요?", example["audience"], max_chars=100) # 대상 입력
        a, b = st.columns(2) # 옵션 두 칸
        channel = a.selectbox("어디에 올릴까요?", list(CHANNELS), format_func=lambda value: CHANNELS[value]["label"]) # 게시 채널 선택
        tone = b.selectbox("어떤 말투로 쓸까요?", ["다정한", "담백한", "활기찬"]) # 말투 선택
        required = st.text_input("꼭 넣을 문구 · 선택", example["required_phrase"], max_chars=30) # 필수 문구 입력
        forbidden = st.text_input("피할 표현 · 쉼표로 구분", "최저가, 건강") # 금지어 입력
        request = st.text_area("원하는 분위기 · 선택", example["request"], max_chars=400) # 창작 방향 입력
        image = st.file_uploader("상품 사진 · 선택 / 5MB 이하", type=["jpg", "jpeg", "png", "webp"]) # 사진 업로드
        submitted = st.form_submit_button("광고 문구 3개 만들기", type="primary", use_container_width=True) # 생성 버튼
    st.caption("글자 수는 서비스 내부 기준이에요. 문자 발송·광고 게시 기능은 포함하지 않아요.") # 지원 범위 안내
if submitted: # 사용자가 생성 버튼을 누른 조건
    try: # 입력 및 연결 오류 처리 영역
        brief = Brief(store=store, product=product, facts=[value.strip() for value in facts.splitlines() if value.strip()], audience=audience, tone=tone, channel=channel, required_phrase=required, forbidden_words=[value.strip() for value in forbidden.split(",") if value.strip()], request=request) # 입력값 검증
        with st.spinner("우리 가게에 어울리는 문구를 쓰고 있어요…"): # 생성 대기 안내
            st.session_state["result"] = generate(brief, image=image.getvalue() if image else None, api_key=key or None) # 실제 광고 생성
    except (ValueError, GenerationError) as error: # 입력 및 생성 실패 처리
        st.error(str(error)) # 수정 가능한 오류 안내
with right: # 생성 결과 영역
    st.subheader("02 / 골라 쓰는 광고 문구") # 결과 제목
    result = st.session_state.get("result") # 현재 생성 결과
    sample = Path("examples/sample_result.json") # 배포용 예제 결과 경로
    if demo and sample.exists(): # 예제 결과가 준비된 조건
        result = json.loads(sample.read_text(encoding="utf-8")) # 예제 결과 불러오기
        st.info("미리 저장한 예시예요. 이 모드에서는 API를 호출하지 않아요.") # 예제 표시
    if result: # 결과가 있을 때의 조건
        if result["ready"]: # 자동 점검 통과 조건
            st.success("형식·필수 문구 자동 점검을 통과했어요. 게시 전 내용은 직접 확인해주세요.") # 통과 안내
        else: # 문제가 남아 있는 조건
            st.warning("수정이 필요한 항목이 있어요. 아래 점검 내용을 확인해주세요.") # 미통과 안내
        for index, item in enumerate(result["bundle"]["variants"], 1): # 광고안 표시 반복
            with st.container(border=True): # 광고 카드
                st.caption(f"광고안 0{index}") # 광고 번호
                st.subheader(item["headline"]) # 광고 제목
                st.write(item["body"]) # 광고 본문
                st.write(item["cta"]) # 행동 유도 문구
                if item["hashtags"]: # 해시태그가 있는 조건
                    st.caption(" ".join(item["hashtags"])) # 해시태그 표시
                st.code("\n".join([item["headline"], item["body"], item["cta"], " ".join(item["hashtags"])]), language=None) # 복사 가능한 원문
        with st.expander("확인 사항과 사용한 사실 보기"): # 점검 상세 영역
            for warning in result["bundle"]["warnings"]: # 확인 사항 반복
                st.write("• " + warning) # 확인 사항 표시
            for issue in result["issues"]: # 자동 점검 문제 반복
                st.write(f"광고안 {issue['variant']}: {issue['detail']}") # 문제 위치 표시
            st.json(result["brief"]["facts"]) # 입력 사실 표시
            st.caption("근거 번호는 모델의 자기 보고이며 사실성 전체를 검증하지 않아요.") # 검증 한계 안내
        st.download_button("문구 내려받기 (.md)", to_markdown(result), "gage-hanjul.md", "text/markdown") # 문구 다운로드
        st.download_button("점검 내역 내려받기 (.json)", json.dumps(result, ensure_ascii=False, indent=2), "gage-hanjul.json", "application/json") # 상세 결과 다운로드
        cost = sum(call["estimated_usd"] for call in result["calls"]) # 합산 추정 비용
        st.caption(f"이 결과의 추정 API 비용 ${cost:.5f} · 캐시 할인 미반영") # 비용 표시
    else: # 아직 결과가 없는 조건
        st.info("왼쪽에서 상품을 소개하고 버튼을 누르면 광고 세 가지가 여기에 보여요.") # 빈 화면 안내
        st.markdown("**상품명과 사실은 정확하게. 표현은 우리 가게답게.**") # 서비스 메시지
