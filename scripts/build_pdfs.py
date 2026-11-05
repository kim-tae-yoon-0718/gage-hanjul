#@title 보고서와 업무일지 PDF 만들기
#@markdown 한글 폰트와 실측 결과로 두 PDF를 만들고 모든 페이지를 PNG로 렌더링해요.
import argparse # 폰트 경로 옵션 도구
import html # 문서 특수 문자를 안전하게 바꾸는 도구
import json # 실험 요약 읽기 도구
from pathlib import Path # 파일 경로 도구
import re # 간단한 문서 표기 변환 도구
import pymupdf as fitz # PDF 렌더링 도구
from reportlab.lib import colors # 문서 색상 도구
from reportlab.lib.enums import TA_LEFT # 본문 정렬 도구
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet # 문서 글꼴 스타일 도구
from reportlab.lib.pagesizes import A4 # A4 용지 크기
from reportlab.pdfbase import pdfmetrics # 한글 글꼴 등록 도구
from reportlab.pdfbase.ttfonts import TTFont # TTF 글꼴 도구
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, KeepTogether # 문서 배치 도구
from reportlab.graphics.shapes import Drawing, Rect, String, Line # 벡터 차트 도구
GREEN = colors.HexColor("#156854") # 주요 색상
INK = colors.HexColor("#20332e") # 본문 색상
PALE = colors.HexColor("#edf3ef") # 표 배경 색상
def register_font(custom: str | None): # 한글 글꼴을 준비하는 함수
    candidates = [Path(custom)] if custom else [Path("C:/Windows/Fonts/malgun.ttf"), Path("/usr/share/fonts/truetype/nanum/NanumGothic.ttf")] # 시스템별 글꼴 후보
    font = next((path for path in candidates if path.exists()), None) # 사용할 글꼴 선택
    if font is None: # 글꼴 누락 조건
        raise SystemExit("한글 TTF 글꼴을 --font 경로로 지정해주세요.") # 해결 방법 안내
    bold = font.with_name("malgunbd.ttf") if font.name == "malgun.ttf" else font # 굵은 글꼴 선택
    pdfmetrics.registerFont(TTFont("Korean", str(font))) # 본문 글꼴 등록
    pdfmetrics.registerFont(TTFont("KoreanBold", str(bold))) # 제목 글꼴 등록
    pdfmetrics.registerFontFamily("Korean", normal="Korean", bold="KoreanBold", italic="Korean", boldItalic="KoreanBold") # 굵기 변환 설정
def styles(): # 문서 스타일을 만드는 함수
    return {"body": ParagraphStyle("body", fontName="Korean", fontSize=9.6, leading=16.3, textColor=INK, spaceAfter=9, wordWrap="CJK"), "h2": ParagraphStyle("h2", fontName="KoreanBold", fontSize=15, leading=21, textColor=GREEN, spaceBefore=18, spaceAfter=11, keepWithNext=True, wordWrap="CJK"), "h3": ParagraphStyle("h3", fontName="KoreanBold", fontSize=11.3, leading=17, textColor=INK, spaceBefore=12, spaceAfter=7, keepWithNext=True, wordWrap="CJK"), "small": ParagraphStyle("small", fontName="Korean", fontSize=8, leading=12, textColor=INK, spaceAfter=8, wordWrap="CJK"), "cell": ParagraphStyle("cell", fontName="Korean", fontSize=8.2, leading=12.2, textColor=INK, wordWrap="CJK"), "cover": ParagraphStyle("cover", fontName="KoreanBold", fontSize=38, leading=49, textColor=INK, spaceAfter=20, wordWrap="CJK"), "subtitle": ParagraphStyle("subtitle", fontName="Korean", fontSize=16, leading=25, textColor=GREEN, spaceAfter=18, wordWrap="CJK")} # 한글 본문과 제목 설정
def markup(text: str) -> str: # 마크다운 일부를 PDF 표기로 바꾸는 함수
    value = html.escape(text) # 특수 문자 처리
    value = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", value) # 강조 표기 변환
    value = re.sub(r"`(.+?)`", r"<b>\1</b>", value) # 파일과 코드 이름 강조
    return value # 안전한 본문 반환
def document_body(path: Path, style: dict) -> list: # 마크다운 문서를 배치 요소로 바꾸는 함수
    lines = path.read_text(encoding="utf-8").splitlines() # 문서 읽기
    flow = [] # 배치 요소 목록
    index = 0 # 현재 줄 위치
    while index < len(lines): # 문서를 끝까지 읽는 반복
        line = lines[index].strip() # 한 줄 문서
        if not line or line.startswith("# "): # 빈 줄과 표지 중복 제목 조건
            index += 1 # 다음 줄 이동
            continue # 중복 제목 제외
        if line.startswith("|"): # 표 시작 조건
            rows = [] # 표 데이터
            while index < len(lines) and lines[index].strip().startswith("|"): # 연속된 표 행 반복
                cells = [cell.strip() for cell in lines[index].strip().strip("|").split("|")] # 열 구분
                if not all(re.fullmatch(r"[: -]+", cell) for cell in cells): # 구분선 제외 조건
                    rows.append([Paragraph(markup(cell), style["cell"]) for cell in cells]) # 줄바꿈 가능한 표 셀
                index += 1 # 표 다음 줄 이동
            count = len(rows[0]) # 표 열 수
            widths = [160] + [335 / (count - 1)] * (count - 1) if count > 1 else [495] # 내용에 맞춘 열 너비
            table = Table(rows, colWidths=widths, repeatRows=1, hAlign="LEFT") # 페이지를 넘길 수 있는 표
            table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), PALE), ("TEXTCOLOR", (0, 0), (-1, 0), GREEN), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#dbe3dd")), ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)])) # 표 색상과 여백
            flow.append(KeepTogether([table, Spacer(1, 12)])) # 작은 표가 페이지 사이에서 나뉘지 않게 추가
            continue # 표 뒤로 이동
        if line.startswith("## "): # 큰 절 제목 조건
            flow.append(Paragraph(markup(line[3:]), style["h2"])) # 절 제목 추가
        elif line.startswith("### "): # 작은 절 제목 조건
            flow.append(Paragraph(markup(line[4:]), style["h3"])) # 작은 제목 추가
        elif line.startswith("- "): # 목록 조건
            flow.append(Paragraph("• " + markup(line[2:]), style["body"])) # 목록 문장 추가
        elif line.startswith("> "): # 기록 안내 조건
            flow.append(Paragraph(markup(line[2:]), style["small"])) # 작은 안내 추가
        else: # 일반 본문 조건
            paragraph = [line] # 연속 본문 시작
            while index + 1 < len(lines) and lines[index + 1].strip() and not lines[index + 1].startswith(("#", "|", "- ", "> ")): # 같은 문단을 모으는 조건
                index += 1 # 다음 줄 이동
                paragraph.append(lines[index].strip()) # 문단에 줄 추가
            flow.append(Paragraph(markup(" ".join(paragraph)), style["body"])) # 본문 단락 추가
        index += 1 # 다음 줄 이동
    return flow # 완성한 본문 배치 반환
def chart(comparison: dict) -> Drawing: # 실제 결과로 표지 차트를 만드는 함수
    drawing = Drawing(495, 190) # 벡터 차트 영역
    for index, (stage, label, color) in enumerate([("baseline", "기본 버전", "#9caea6"), ("evidence", "개선 1 · 사실 원장", "#72a18d"), ("repair", "개선 2 · 단일 수정", "#156854")]): # 버전별 막대 반복
        y = 140 - index * 56 # 막대 세로 위치
        value = comparison[stage]["all_pass"] # 실제 통과율
        drawing.add(String(0, y + 9, label, fontName="Korean", fontSize=10, fillColor=INK)) # 버전 이름
        drawing.add(Rect(145, y, 270, 30, fillColor=PALE, strokeColor=None)) # 기준 배경 막대
        drawing.add(Rect(145, y, 270 * value, 30, fillColor=colors.HexColor(color), strokeColor=None)) # 통과율 막대
        drawing.add(String(430, y + 9, f"{value * 100:.1f}%", fontName="KoreanBold", fontSize=13, fillColor=GREEN)) # 정확한 통과율 숫자
    return drawing # 차트 반환
def footer(canvas, doc): # 모든 페이지의 머리말과 꼬리말 함수
    canvas.saveState() # 캔버스 상태 보존
    width, height = A4 # 용지 크기
    canvas.setStrokeColor(colors.HexColor("#d9e2dc")) # 구분선 색상
    canvas.line(50, height - 35, width - 50, height - 35) # 머리말 구분선
    canvas.setFont("Korean", 7.5) # 작은 글꼴
    canvas.setFillColor(GREEN) # 머리말 색상
    canvas.drawString(50, height - 25, "GAGE HANJUL / 개인 고급 프로젝트") # 문서 머리말
    canvas.setFillColor(colors.HexColor("#75847c")) # 꼬리말 색상
    canvas.drawString(50, 25, "실제 수행·작성 2026.11.05 / 고정 평가 v1") # 실제 수행 정보
    canvas.drawRightString(width - 50, 25, str(doc.page)) # 페이지 번호
    canvas.restoreState() # 캔버스 상태 복원
def build_report(style: dict, comparison: dict): # 최종 보고서를 만드는 함수
    flow = [Spacer(1, 34), Paragraph("우리 가게의 매력을,<br/>한 줄 더.", style["cover"]), Paragraph("가게한줄 프로젝트 보고서", style["subtitle"]), Paragraph("완성된 기본 서비스와 두 번의 개별 개선 실험<br/>OpenAI API · 로컬 실행 · 사용자 GPU 사용 없음", style["body"]), Spacer(1, 18), chart(comparison), Spacer(1, 14)] # 표지 구성
    flow.append(Paragraph("31/36 묶음 전체 통과 · 기본 14/36 대비 +47.22%p", style["h3"])) # 핵심 실측 성과
    flow.append(Paragraph("최종 구조는 사실 원장과 검증 실패 시 최대 1회 수정입니다. 여전히 5개 묶음에 오류가 남았으며, 자동 점검이 의미 전체의 사실성을 보장하지 않습니다.", style["body"])) # 해석 범위
    flow.append(Paragraph("정식 비교 90회 · 추정 $0.100846<br/>실제 수행·실험·작성일 2026년 11월 5일", style["small"])) # 실측 수행 정보
    flow.append(PageBreak()) # 본문을 새 페이지에서 시작
    flow.append(Paragraph("서비스 화면과 사용자 흐름", style["h2"])) # 화면 소개 제목
    photo = Path("docs/images/app.jpg") # 실제 Chrome 검증 화면
    if photo.exists(): # 화면 캡처가 있는 조건
        with fitz.open(photo) as image_doc: # 이미지 크기 확인 도구
            rect = image_doc[0].rect # 화면 종횡비
        flow.append(Image(str(photo), width=495, height=495 * rect.height / rect.width)) # 비율을 유지한 화면 이미지
    flow.append(Paragraph("실제 Chrome에서 상품 입력 → 광고 생성 → 자동 점검 통과 표시 → JSON 내려받기를 확인한 화면입니다. 예시 모드가 아닌 실제 생성 결과입니다.", style["small"])) # 검증 근거 설명
    flow.append(Paragraph("입력 → 사실 원장 → 광고 3안 → 공통 검증 → 실패 시 1회 수정 → 사용자 검토", style["h3"])) # 파이프라인 개요
    flow.extend(document_body(Path("docs/report.md"), style)) # 보고서 본문 추가
    SimpleDocTemplate("output/pdf/project_report.pdf", pagesize=A4, rightMargin=50, leftMargin=50, topMargin=55, bottomMargin=48, title="가게한줄 프로젝트 보고서", author="가게한줄 프로젝트").build(flow, onFirstPage=footer, onLaterPages=footer) # 보고서 PDF 생성
def build_worklog(style: dict): # 업무일지 PDF 사본 생성 함수
    flow = [Paragraph("가게한줄 업무일지", style["cover"]), Paragraph("11월 1일 - 11월 5일 / 단계별 회고", style["subtitle"]), Paragraph("실제 작업과 기록은 2026년 11월 5일에 진행했습니다. 요청한 다섯 날짜로 진행 단계를 나눈 회고 기록입니다. 과거 날짜의 실제 수행 이력이나 사용자 개인의 감정을 증명하지 않습니다.", style["body"])] # 업무일지 표지
    flow.extend(document_body(Path("docs/worklog.md"), style)) # 일지 본문 추가
    SimpleDocTemplate("output/pdf/worklog.pdf", pagesize=A4, rightMargin=50, leftMargin=50, topMargin=55, bottomMargin=48, title="가게한줄 업무일지", author="가게한줄 프로젝트").build(flow, onFirstPage=footer, onLaterPages=footer) # 업무일지 PDF 생성
def render_all(): # 모든 PDF를 PNG로 확인하는 함수
    target = Path("tmp/pdf_qa") # 렌더링 저장 위치
    target.mkdir(parents=True, exist_ok=True) # 검토 폴더 생성
    for source in Path("output/pdf").glob("*.pdf"): # 최종 문서 반복
        with fitz.open(source) as document: # PDF 열기
            for page in document: # 모든 페이지 반복
                page.get_pixmap(matrix=fitz.Matrix(1.2, 1.2)).save(target / f"{source.stem}-{page.number + 1:02d}.png") # 페이지별 PNG 렌더링
            print(f"{source}: {len(document)} pages") # 문서 페이지 수 안내
def main(): # 문서 생성 실행 함수
    parser = argparse.ArgumentParser() # 옵션 도구
    parser.add_argument("--font") # 사용자 한글 TTF 글꼴 옵션
    args = parser.parse_args() # 옵션 읽기
    register_font(args.font) # 한글 폰트 등록
    Path("output/pdf").mkdir(parents=True, exist_ok=True) # 제출 PDF 폴더 생성
    comparison = json.loads(Path("experiments/comparison.json").read_text(encoding="utf-8")) # 실제 결과 읽기
    style = styles() # 공통 문서 스타일
    build_report(style, comparison) # 보고서 생성
    build_worklog(style) # 업무일지 사본 생성
    render_all() # 모든 페이지 렌더링
if __name__ == "__main__": # 직접 실행 조건
    main() # 문서 생성 실행
