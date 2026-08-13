"""산업 태세 — **현재 산업은 정책이 맞춰주고, 미래 산업은 정책이 유도한다.**

이 한 줄이 이 도구의 판정 기준을 둘로 가른다.

- **대응형(현재 산업)**: 실측 수요가 이미 있다. 정책은 그 수요를 *맞춰야* 한다.
  → 물을 질문은 "수요를 덮는 사업이 있는가". 못 덮으면 **대응 실패**다.
- **유도형(미래 산업)**: 수요가 아직 없다. 정책이 수요를 *만들어야* 한다.
  → 물을 질문은 "만들 근거가 있는가". 수요가 없다는 사실 자체는 흠이 아니다.

두 산업에 같은 질문을 하면 반드시 한쪽이 틀린다. 유도형에 "수요 근거를 대라"고 하면
미래 산업 정책은 전부 부결되고, 대응형에 "유도 근거를 대라"고 하면 눈앞의 인력난을 놓친다.

**태세는 우리가 정하지 않는다.** 조사자 B의 수요신호가 정한다(아래 `posture`). 새 신호가
들어오면 태세가 저절로 바뀌고, 그와 함께 판정 질문도 바뀐다.
"""

PRINCIPLE = "현재 산업은 정책이 맞춰주고, 미래 산업은 정책이 유도한다."

# 6대 전략산업 + 광역 공통. 키워드는 사업명·요약에서 산업을 되찾는 데 쓴다.
INDUSTRY_KEYWORDS = {
    "바이오": ["바이오", "제약", "세포", "백신", "의약", "NIBRT", "오가노이드"],
    "반도체": ["반도체", "팹리스", "패키징", "후공정", "시스템반도체"],
    "로봇": ["로봇"],
    "디지털데이터": ["디지털", "데이터", "인공지능", "AI", "SW", "소프트웨어", "양자", "ICT"],
    "미래차": ["미래차", "자동차", "전기차", "모빌리티", "충전인프라", "부품기업"],
    "항공": ["항공", "공항", "MRO", "UAM", "정비", "영종"],
}
INDUSTRIES = list(INDUSTRY_KEYWORDS)

# 태세 판정에 쓰는 근거 문턱. **실측 수요**로 인정하는 조건이다.
#   - trend == SUSTAINED : 두 시점 이상에서 반복 확인 (단발 SPIKE·전망 FORECAST 제외)
#   - grade in (A, B)    : 공공 통계 원자료·공식 계획서 (C=언론 정성서술, D=자기정당화 제외)
# 둘 다 만족하는 신호가 하나라도 있으면 대응형이다.
MEASURED_TRENDS = {"SUSTAINED"}
MEASURED_GRADES = {"A", "B"}

RESPONSIVE, INDUCING, UNDECIDED = "대응형", "유도형", "판단보류"

POSTURE_QUESTION = {
    RESPONSIVE: "산업이 이미 필요로 하는 것을 이 사업이 덮는가",
    INDUCING: "아직 없는 수요를 만들 근거가 이 사업에 있는가",
    UNDECIDED: "이 산업의 수요를 조사한 자료가 아직 없다",
}
POSTURE_LABEL = {
    RESPONSIVE: "대응형 — 현재 산업, 정책이 맞춰준다",
    INDUCING: "유도형 — 미래 산업, 정책이 이끈다",
    UNDECIDED: "판단보류 — 수요 조사 자체가 없다",
}


def industry_of(text):
    """사업명·요약에서 전략산업을 되찾는다. 겹치면 먼저 걸린 것을 쓴다."""
    t = text or ""
    for ind, words in INDUSTRY_KEYWORDS.items():
        if any(w in t for w in words):
            return ind
    return None


def _industries_of_signal(row):
    """B2의 strategic_industry는 '바이오+디지털데이터'처럼 복합값이 온다."""
    raw = (row.get("strategic_industry") or "").strip()
    if not raw or raw == "공통":
        return []
    return [p.strip() for p in raw.split("+") if p.strip() in INDUSTRY_KEYWORDS]


def posture(industry, b2_rows):
    """산업 하나의 태세를 **수요신호만 보고** 정한다.

    b2_rows: B2 원본 행들(dict). 판정 근거를 함께 돌려주므로 화면에서 "왜 유도형인가"를
    바로 답할 수 있다.
    """
    mine = [r for r in b2_rows if industry in _industries_of_signal(r)]
    measured = [r for r in mine
                if (r.get("sustained_or_spike") or "").strip() in MEASURED_TRENDS
                and (r.get("evidence_grade") or "").strip() in MEASURED_GRADES]
    if measured:
        state = RESPONSIVE
        why = (f"반복 확인된 공공자료 수요신호 {len(measured)}건 — "
               + ", ".join(r["signal_id"] for r in measured))
    elif mine:
        state = INDUCING
        why = (f"수요신호 {len(mine)}건이 있으나 전부 단발이거나 언론·자기정당화 근거다 "
               f"({', '.join(sorted({(r.get('sustained_or_spike') or '?') + '/' + (r.get('evidence_grade') or '?') for r in mine}))})"
               " — 실측 수요로 보기 어렵다")
    else:
        state = UNDECIDED
        why = "이 산업을 다루는 수요신호가 조사 원장에 없다"
    return {"industry": industry, "posture": state, "question": POSTURE_QUESTION[state],
            "label": POSTURE_LABEL[state], "why": why,
            "signals": [r["signal_id"] for r in mine],
            "measured": [r["signal_id"] for r in measured]}


def postures(b2_rows):
    return {ind: posture(ind, b2_rows) for ind in INDUSTRIES}


# ─────────────────────────────────────────────────────────────
# 유도형 산업에 요구하는 근거 3종
#
# "미래 산업이라 수요가 없다"는 말이 무근거 사업의 면죄부가 되면 안 된다. 실제로 인천
# 시의회는 양자바이오 사업에 "기업 수요에 대한 구체적 설명이 필요하다"고 지적했다(D-110).
# 그래서 유도형에는 수요 대신 **다른 근거 3종**을 묻는다. 없으면 없다고 표시할 뿐,
# 있다고 지어내지 않는다.
# ─────────────────────────────────────────────────────────────
INDUCEMENT_TESTS = [
    ("상위계획", "이 산업을 명시한 상위 계획·전략 문서가 있는가"),
    ("출구조건", "몇 년 안에 무엇이 안 나오면 접는지 사업에 적혀 있는가"),
    ("선점논거", "다른 지역이 이미 하고 있는지 확인했는가"),
]


def inducement_evidence(card, plans):
    """유도형 사업의 근거 3종을 카드와 계획문서로 채점한다.

    plans: 계획·전략 층위 카드 목록(예산 미부착). 산업이 같은 계획이 있으면 상위계획 근거로 본다.
    """
    ind = industry_of((card.get("name") or "") + str(card.get("summary") or ""))
    hit_plans = [p for p in plans
                 if industry_of((p.get("name") or "") + str(p.get("summary") or "")) == ind]
    kpi = card.get("output_kpi")
    return [
        {"test": "상위계획", "ok": bool(hit_plans),
         "detail": ("상위 계획 " + ", ".join(p["name"] for p in hit_plans[:2])) if hit_plans
                   else "이 산업을 명시한 상위 계획 문서를 원장에서 찾지 못했다"},
        {"test": "출구조건", "ok": bool(kpi),
         "detail": f"성과지표: {kpi}" if kpi
                   else "성과지표가 원문에 없어 언제 접을지 판단할 근거가 없다"},
        {"test": "선점논거", "ok": False,
         "detail": "타 지역 중복 여부는 조사 원장에 없다 — 담당자가 직접 확인해야 한다"},
    ]
