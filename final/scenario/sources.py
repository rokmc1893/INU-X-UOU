"""자료를 어디서 찾나 — 산업과 「비어 있는 칸」을 출처에 잇는다.

담당자가 실제로 어려워하는 것은 비교가 아니라 **관련 자료를 찾는 일**이다.
그래서 이 안내판은 출처를 그냥 나열하지 않고 **비어 있는 칸에서 출발한다** —
「돈이 0÷2로 비어 있다」면 돈 자료를 주는 곳만 보여준다.

**되는 곳과 막힌 곳을 같이 보여준다.** 2026-08-14에 직접 접속해 확인한 결과이며,
막힌 곳을 지우면 "여기만 보면 다 된다"로 읽힌다. 특히 막힌 두 곳(인천연구원·인천TP)이
하필 「기업이 무엇을 필요로 하는가」를 담고 있어, 이 사실 자체가 판정의 한계를 설명한다.
"""

OK = "ok"                # 지금 열린다
KEY = "key_needed"       # 열리지만 인증키가 있어야 한다
BLOCKED = "blocked"      # 접속이 막혀 있다
MANUAL = "manual"        # 온라인으로 못 구한다 — 정보공개청구

STATUS_LABEL = {
    OK: "지금 열림",
    KEY: "인증키 필요",
    BLOCKED: "접속 막힘",
    MANUAL: "청구해야 함",
}
CHECKED_ON = "2026-08-14"

# 산업별 검색어 — 검색창에 그대로 넣으면 된다
TERMS = {
    "바이오": ["바이오", "바이오공정", "제약", "세포"],
    "반도체": ["반도체", "팹리스", "패키징"],
    "로봇": ["로봇"],
    "항공": ["항공", "항공정비", "MRO"],
    "미래차": ["미래차", "자동차부품", "전기차"],
    "디지털데이터": ["인공지능", "데이터", "디지털"],
}

# gives = 이 출처가 채워 줄 수 있는 「필요한 것」 (fit.needs.NEEDS와 같은 말)
# search = 검색어를 붙여 바로 열리는 주소 (`{q}` 자리에 검색어가 들어간다). None이면 사이트만 연다.
SOURCES = [
    dict(key="bizinfo", name="기업마당", status=KEY,
         url="https://www.bizinfo.go.kr",
         search="https://www.bizinfo.go.kr/web/lay1/bbs/S1T122C128/AS/74/list.do"
                "?searchCnd=1&searchWrd={q}",
         gives=["기업 자금", "기술 개발", "팔 곳", "일할 사람"],
         what="중앙부처와 지자체가 하는 기업지원사업이 한곳에 모여 있습니다",
         note="검색은 지금 바로 열립니다. 자동으로 긁어 오려면 공공데이터포털에서 "
              "인증키를 받아야 합니다."),
    dict(key="kosis", name="국가통계포털 KOSIS", status=OK,
         url="https://kosis.kr",
         search="https://kosis.kr/search/search.do?query={q}",
         gives=["일할 사람", "거래할 기업"],
         what="사업체 수·종사자 수 같은 공식 통계를 봅니다",
         note="인천만 따로 나오지 않는 통계가 많습니다. 권역까지만 공개된 것도 있습니다."),
    dict(key="incheon", name="인천시 누리집", status=OK,
         url="https://www.incheon.go.kr",
         search=None,
         gives=["일할 사람", "기술 개발", "기업 자금", "팔 곳", "거래할 기업", "공간·장비"],
         what="고시·공고·보도자료. 사업의 원문이 여기 있습니다",
         note="검색창에 검색어를 넣으세요. 주소로 바로 여는 방법은 확인하지 못했습니다."),
    dict(key="youth", name="온통청년", status=OK,
         url="https://www.youthcenter.go.kr",
         search=None,
         gives=["일할 사람"],
         what="청년정책이 한곳에 모여 있습니다",
         note="접속이 느릴 때가 있습니다."),
    dict(key="elis", name="자치법규정보시스템", status=OK,
         url="https://www.elis.go.kr",
         search=None,
         gives=["행정 절차"],
         what="조례·규칙. 사업의 법적 근거를 확인합니다",
         note="사업을 새로 만들 때 근거 법령이 있는지 보는 곳입니다."),
    dict(key="data", name="공공데이터포털", status=OK,
         url="https://www.data.go.kr",
         search=None,
         gives=["일할 사람", "기술 개발", "기업 자금", "팔 곳", "거래할 기업", "공간·장비", "행정 절차"],
         what="기관들이 여는 자료와 API 목록",
         note="기업마당 인증키도 여기서 받습니다."),
    dict(key="itp", name="인천테크노파크", status=BLOCKED,
         url="https://www.itp.or.kr",
         search=None,
         gives=["기술 개발", "공간·장비", "일할 사람"],
         what="기업 실태조사와 지원사업 공고",
         note="보안 설정이 낡아 바깥에서 자동으로 못 엽니다. 브라우저로는 열릴 수 있으니 "
              "직접 열어 본문을 복사해 「자료 올리기」에 넣으세요."),
    dict(key="ii", name="인천연구원", status=BLOCKED,
         url="https://www.ii.re.kr",
         search=None,
         gives=["일할 사람", "기업 자금", "거래할 기업", "기술 개발"],
         what="기업이 무엇을 필요로 하는지 조사한 보고서",
         note="접속이 막혀 있고, 열리는 보고서도 사진으로 스캔한 PDF가 많아 글자를 "
              "못 읽습니다. 우리가 지금 「기업 자금」 자료를 못 채우는 가장 큰 이유입니다."),
    dict(key="lofin", name="지방재정365", status=BLOCKED,
         url="https://lofin.mois.go.kr",
         search=None,
         gives=["행정 절차"],
         what="세부사업별 예산·집행 내역",
         note="접속이 되지 않습니다. 인천시 예산서를 직접 받는 편이 빠릅니다."),
    dict(key="open", name="정보공개청구", status=MANUAL,
         url="https://www.open.go.kr",
         search=None,
         gives=["행정 절차", "기업 자금"],
         what="내부 방침서·예산 심사 가감표·성과평가 세부 점수표",
         note="공개된 곳이 없어 청구해야 합니다. 무엇을 청구할지는 아래 「청구 문안」을 쓰세요."),
]

# 청구 문안 — 조사자 A가 미확인으로 남긴 것들(A5 Q1~Q5)과 같은 대상이다
CLAIM_TEXTS = {
    "기업 자금": "○○년도 {industry} 분야 세부사업 예산 심사 과정의 증액·감액 사유서",
    "행정 절차": "{industry} 분야 신규사업 유사·중복 검토서 및 부서 협의 요청서",
    "일할 사람": "{industry} 분야 인력양성 사업의 수료·취업 실적 및 기업 수요조사서",
}


def _q(term):
    from urllib.parse import quote
    return quote(term)


def for_industry(industry, need=None):
    """이 산업 자료를 어디서 찾나. need를 주면 그 칸을 채울 곳만 골라 준다."""
    terms = TERMS.get(industry, [industry] if industry else [])
    term = terms[0] if terms else ""
    out = []
    for s in SOURCES:
        if need and need not in s["gives"]:
            continue
        link = s["search"].format(q=_q(term)) if (s["search"] and term) else s["url"]
        out.append({**s, "link": link, "terms": terms,
                    "direct": bool(s["search"] and term),
                    "status_label": STATUS_LABEL[s["status"]]})
    # 지금 열리는 곳을 먼저, 막힌 곳을 뒤로 — 지우지는 않는다
    order = {OK: 0, KEY: 1, BLOCKED: 2, MANUAL: 3}
    return sorted(out, key=lambda s: order[s["status"]])


def claim_text(need, industry):
    """정보공개청구에 그대로 쓸 문안. 없으면 None."""
    t = CLAIM_TEXTS.get(need)
    return t.format(industry=industry or "해당") if t else None


def summary():
    """되는 곳 / 막힌 곳 몇 개인지 — 화면에 정직하게 적는다."""
    c = {}
    for s in SOURCES:
        c[s["status"]] = c.get(s["status"], 0) + 1
    return c
