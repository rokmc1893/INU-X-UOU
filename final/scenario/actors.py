"""A1 액터 레지스트리 — 누가 결정하고 어느 과와 협의하는가.

산업 구분이 A와 B가 다르다. **판정은 B 기준, 협의처는 A 기준**으로 간다(SCAFFOLD §4).
로봇과 항공은 B에서 둘이지만 A에서는 한 과(로봇항공과)다.

**미해결**: A1이 두 버전이고 부서 체계가 충돌한다(조직개편 전/후). 앱 풀은 개편 **전**
버전이다. 화면에 "조직개편 전 기준, 발송 전 재확인"이라고 반드시 적는다.
→ `02_조사자료/RESEARCH_TODO.md` P0-2.
"""
from engine.refdata import _rows

SOURCE = "조사자 A · A1_actor_registry.csv (조직개편 전 기준)"
CAVEAT = ("부서 체계는 조직개편 <b>전</b> 기준입니다. 개편 후 명칭이 바뀌었을 수 있으니 "
          "공문 발송 전 조직도로 재확인하세요.")

# B 판정 산업 → A 부서 기준. '물류·항만'(항만공항정책과)은 B에 대응 산업이 없어 여기 없다.
B_TO_A = {
    "바이오": dict(a_industry="바이오", team="반도체바이오과", bureau="미래산업국"),
    "반도체": dict(a_industry="반도체", team="반도체바이오과", bureau="미래산업국"),
    "로봇": dict(a_industry="로봇·항공", team="로봇항공과", bureau="미래산업국"),
    "항공": dict(a_industry="로봇·항공", team="로봇항공과", bureau="미래산업국"),
    "미래차": dict(a_industry="미래모빌리티", team="미래모빌리티과", bureau="미래산업국"),
    # 산업명과 부서명이 일치하지 않는 유일한 케이스 — 스마트시티·AI의 소관은 AI블록체인과다
    "디지털데이터": dict(a_industry="스마트시티·AI", team="AI블록체인과", bureau="미래산업국"),
}

# A3 3단계 검토자 — 원문 규칙 그대로
YOUTH_REVIEWER = "청년정책담당관"
RISE_REVIEWER = "교육협력담당관"
EVAL_REVIEWER = "평가담당관"

_YOUTH_WORDS = ("청년", "취업", "일경험", "구직", "인턴")
_RISE_WORDS = ("RISE", "라이즈", "대학", "학과", "산학")


def registry():
    """A1 원장. **마지막 행(인천테크노파크)은 필드가 11개**로 헤더(12개)보다 하나 적어
    컬럼이 밀린다 — team이 비어 있는 행으로 걸러낸다.
    """
    out = []
    for r in _rows("A1_actor_registry.csv"):
        if not (r.get("team") or "").strip():
            continue  # 필드 수가 어긋난 행 — 억지로 보정하지 않고 뺀다
        out.append(r)
    return out


def _find(team):
    return next((r for r in registry() if (r.get("team") or "").strip() == team), None)


def _industries(card):
    raw = (card.get("strategic_industry") or "").strip()
    return [p.strip() for p in raw.split("+") if p.strip() in B_TO_A]


def consult_for(card):
    """이 사업으로 공문을 보낼 부서. 산업이 미상이면 빈 목록 — 추측해서 안내하지 않는다."""
    out, seen = [], set()
    for ind in _industries(card):
        m = B_TO_A[ind]
        if m["team"] in seen:
            continue
        seen.add(m["team"])
        row = _find(m["team"]) or {}
        out.append(dict(
            b_industry=ind, a_industry=m["a_industry"],
            team=m["team"], bureau=m["bureau"],
            decision_right=(row.get("decision_right") or "").strip() or "미확인",
            contact=(row.get("public_contact") or "").strip() or "미확인",
            source_url=(row.get("source_url") or "").strip(),
            as_of=(row.get("as_of") or "").strip()))
    return out


def reviewers_for(card):
    """A3 3단계 검토자. 평가담당관은 항상, 나머지는 사업 성격에 따라 붙는다."""
    text = (card.get("name") or "") + " " + str(card.get("summary") or "")
    out = []
    if any(w in text for w in _YOUTH_WORDS):
        out.append(dict(who=YOUTH_REVIEWER, why="청년 사업이라 A3 3단계 검토자에 포함됩니다"))
    if any(w in text for w in _RISE_WORDS):
        out.append(dict(who=RISE_REVIEWER, why="대학·RISE 연계라 A3 3단계 검토자에 포함됩니다"))
    out.append(dict(who=EVAL_REVIEWER, why="A3 3단계의 상시 검토자입니다"))
    return out


def unknowns():
    return [
        "A1이 두 버전이고 부서 체계가 충돌합니다(조직개편 전/후). 지금은 개편 전 기준입니다.",
        "A1 마지막 행(인천테크노파크)은 필드 수가 어긋나 협의처 산출에서 제외했습니다.",
        "A의 '물류·항만'(항만공항정책과)은 우리 판정 산업에 대응하는 것이 없습니다.",
    ]
