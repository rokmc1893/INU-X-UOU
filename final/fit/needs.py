"""산업이 필요로 하는 것 ↔ 사업이 주는 것 — 직무 하나가 아니라 **7가지 지원 유형**으로 맞춘다.

여태 이 도구는 수요와 사업을 **직무**로만 맞췄다. 그래서 조사 원장 78행 중 인력 수요
26행(33%)만 대조됐고, 시설·기술·공급망·금융·판로 수요 52행은 아예 대조 대상이 아니었다.
사업 쪽도 마찬가지로 드론 실증도시·바이오클러스터·해외진출 지원처럼 직무가 없는 사업이
판정에서 통째로 빠졌다.

여기서 축을 넓힌다. 양쪽 어휘는 이미 있었다 — 조사자 B의 `problem_type`이 수요의 종류를
말하고, 우리 `intervention_type`이 사업이 주는 것을 말한다. 잇는 규칙만 없었을 뿐이다.

**맞추는 조건은 둘이다: 같은 산업 ∧ 같은 지원 유형.** 직무는 인력 유형 안에서만 쓴다.
"""

# 지원 유형 7종. 조사자 C의 성과축(C1)이 말하는 실패 지점과 1:1로 붙는다.
NEEDS = ["인력", "기술", "금융", "판로", "공급망", "시설", "행정"]

NEED_LABEL = {
    "인력": "사람이 없다",
    "기술": "기술·연구개발이 모자란다",
    "금융": "돈을 못 구한다",
    "판로": "팔 곳이 없다",
    "공급망": "받쳐 줄 기업·기관이 없다",
    "시설": "쓸 공간·장비가 없다",
    "행정": "행정이 못 따라간다",
}

# B2 problem_type → 지원 유형. 먼저 걸리는 것을 쓴다(순서가 우선순위다).
_NEED_WORDS = [
    ("행정", ["집행지연", "행정경계", "수요조사", "데이터 공백", "계획목표", "정책유행", "정책 축소"]),
    ("시설", ["시설", "산단", "분양", "공간"]),
    ("공급망", ["공급망", "밸류체인", "산업구조", "단일고객", "생태계", "산업기반"]),
    ("기술", ["기술", "R&D", "흡수역량"]),
    ("금융", ["금융", "자금", "투자"]),
    ("판로", ["판로", "수출", "해외", "시장구조", "수요처"]),
    ("인력", ["인력", "인재", "채용", "교육", "취업", "일자리", "근속"]),
]

# 수요가 아닌 행 — 규모를 말하거나(맥락지표), 수요가 없다고 말하거나(역방향), 현원을 말한다(모수).
# 이걸 수요로 세면 "크다"가 "모자란다"로 둔갑한다.
NOT_A_NEED = ["맥락지표", "모수", "수요부재", "수요신호 부재", "역방향", "지원공급 한도",
              "물량-생산목표", "기업수요-진출의향", "전환 리스크",
              "공급실적", "이용실적"]  # 배출 인원·이용 건수는 공급 지표다


def need_of_signal(problem_type):
    """수요신호 한 줄이 말하는 지원 유형. 수요가 아닌 행은 None."""
    pt = problem_type or ""
    if any(m in pt for m in NOT_A_NEED):
        return None
    for need, words in _NEED_WORDS:
        if any(w in pt for w in words):
            return need
    return None


# 사업이 주는 것(intervention_type) → 덮을 수 있는 지원 유형.
# 한 수단이 두 유형을 덮는 경우가 있다 — 알선·매칭은 사람도 붙이고 기업도 붙인다.
MEANS_COVERS = {
    "교육훈련": ["인력"],
    "현금지원": ["인력"],
    "현물·물품대여": ["인력"],
    "알선·매칭": ["인력", "판로"],
    "상담·컨설팅": ["기술", "판로"],
    "시설·인프라": ["시설"],
    "기업보조금": ["금융"],
    "R&D·기술지원": ["기술"],
    "실증·시범": ["기술"],
    "네트워크·협의체": ["공급망"],
    "판로·해외진출": ["판로"],
}


PLAN_WORDS = ("기본계획", "종합계획", "시행계획", "전략", "육성방안", "로드맵", "추진계획")


def is_plan(card):
    """계획·전략 문서인가. **예산이 붙지 않으므로 수요를 덮을 수 없다.**

    이걸 빼지 않으면 「인천형 라이즈(i-RISE) 기본계획」이 미래차 인력 수요를 덮는다고
    나온다. 계획은 방향을 정할 뿐 돈을 쓰지 않는다.
    """
    return any(w in (card.get("name") or "") for w in PLAN_WORDS)


def needs_covered_by(card):
    """이 사업이 덮을 수 있는 지원 유형. 수단이 원문에 없으면 빈 목록 — 추측하지 않는다."""
    if is_plan(card):
        return []
    return list(MEANS_COVERS.get(card.get("intervention_type") or "", []))


def _inds(value):
    """'바이오+디지털데이터' 같은 복합값을 쪼갠다 (B_README: 배타적 분류 아님)."""
    return {p.strip() for p in (value or "").split("+") if p.strip()}


def industries_match(card, signal_industry):
    """같은 산업인가.

    **사업의 산업이 비어 있으면 덮는다고 보지 않는다.** 비어 있는 것은 '모든 산업'이 아니라
    '모른다'이기 때문이다. 이걸 '전부 해당'으로 두었더니 청년일자리 사업인 「대학일자리플러스
    센터 운영 지원」이 바이오 금융 수요를 덮는다고 나왔다.

    '공통'은 다르다 — 전략산업 총괄 계획처럼 **원문이 명시적으로 전 산업 대상**이라고 밝힌
    것이므로 어느 산업과도 짝이 된다. 수요 쪽의 '공통'(시도 단위 신호)도 마찬가지다.
    """
    a, b = _inds(card.get("strategic_industry")), _inds(signal_industry)
    if "공통" in a or "공통" in b or not b:
        return True
    if not a:
        return False  # 사업의 산업 미상 — 덮는다고 단정하지 않는다
    return bool(a & b)


def coverage(cards, b2_rows):
    """수요 하나하나에 대해 **덮는 사업이 있는가**를 가린다.

    돌려주는 각 항목:
      signal_id / industry / need / grade / trend / value / limit
      covers      같은 산업 ∧ 같은 지원 유형인 사업 목록
      generic     지원 유형은 맞지만 산업이 다르거나 미상인 사업 수
      verdict     covered | uncovered | not_a_need
    """
    out = []
    for r in b2_rows:
        need = need_of_signal(r.get("problem_type"))
        item = {
            "signal_id": (r.get("signal_id") or "").strip(),
            "industry": (r.get("strategic_industry") or "").strip(),
            "problem_type": (r.get("problem_type") or "").strip(),
            "need": need,
            "grade": (r.get("evidence_grade") or "").strip(),
            "trend": (r.get("sustained_or_spike") or "").strip(),
            "value": f"{r.get('value','')} {r.get('unit','')}".strip(),
            "limit": (r.get("proxy_limit") or "").strip(),
            "source_url": (r.get("source_url") or "").strip(),
        }
        if need is None:
            out.append({**item, "covers": [], "generic": 0, "verdict": "not_a_need"})
            continue
        if need == "행정":
            # 집행지연·수요조사 노후화·데이터 공백은 **사업으로 덮는 것이 아니다.**
            # 공백으로 세면 "13건이 안 덮였다"는 잘못된 경보가 된다. 담당자가 처리할 과제로 뺀다.
            out.append({**item, "covers": [], "generic": 0, "verdict": "admin_task"})
            continue
        hit, gen = [], 0
        for c in cards:
            if need not in needs_covered_by(c):
                continue
            if industries_match(c, item["industry"]):
                hit.append(c["policy_id"])
            else:
                gen += 1
        out.append({**item, "covers": hit, "generic": gen,
                    "verdict": "covered" if hit else "uncovered"})
    return out


def unmatched_cards(cards):
    """수단이 원문에 없어 어떤 수요와도 맞출 수 없는 사업.

    '덮는 사업이 없다'와 '수단을 못 읽었다'는 다르다. 이 목록을 숨기면 공백 판정이 실제보다
    커 보인다.
    """
    return [c for c in cards if not needs_covered_by(c)]


def summary(cards, b2_rows):
    cov = coverage(cards, b2_rows)
    real = [c for c in cov if c["verdict"] in ("covered", "uncovered")]
    return {
        "signals_total": len(cov),
        "needs": len(real),
        "not_a_need": sum(1 for c in cov if c["verdict"] == "not_a_need"),
        "admin_task": sum(1 for c in cov if c["verdict"] == "admin_task"),
        "covered": sum(1 for c in real if c["verdict"] == "covered"),
        "uncovered": sum(1 for c in real if c["verdict"] == "uncovered"),
        "cards_total": len(cards),
        "cards_unmatchable": len(unmatched_cards(cards)),
    }
