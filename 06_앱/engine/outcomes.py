"""산업·정책 연계가 끊겼을 때 생기는 7가지 문제 — 조사자 C의 C1 성과축을 화면의 뼈대로 쓴다.

지금까지 이 앱은 일자리 파이프라인(교육훈련→…→정착) 한 축으로만 판정했다. 그런데
C1의 7개 축 중 일자리는 **5순위 하나뿐**이고, C가 1·2순위로 꼽은 것은 예산 비효율과
산업 생태계다. 결정로그 D-001이 정한 타겟(산업·정책 연계 부족)과도 어긋나 있었다.

여기서는 축을 지어내지 않는다. `C1_outcome_feasibility_matrix.csv`를 그대로 읽고, 축마다
**우리가 지금 무엇을 판정하는지 / 못 하면 왜 못 하는지**만 붙인다. 판정 못 하는 축을
숨기면 "7개 중 1개만 본다"는 사실이 감춰진다.
"""
from .refdata import _rows

# 축 → 우리 판정 모듈. covered:
#   full    이 축을 정면으로 판정한다
#   partial 일부만 본다
#   none    판정 수단이 없다 (왜 없는지 gap에 적는다)
AXIS_BINDING = {
    "정책 예산의 비효율적 사용": {
        "covered": "partial",
        "module": "예산 원장 대조 — 매칭상태·소관 불일치·중복 편성 의심",
        "finding_keys": ["budget_confirmed", "budget_unverified",
                         "budget_conflicts", "dept_mismatch"],
        "gap": "조사자 C가 대조를 마친 사업이 10건뿐이라, 나머지는 '예산이 없다'가 아니라 "
               "'아직 대조하지 못했다'로 남는다",
    },
    "산업 생태계 형성 어려움": {
        "covered": "partial",
        "module": "사업 간 역할중첩·인계 단절 판정",
        "finding_keys": ["handoff_breaks", "overlaps_harmful",
                         "overlaps_intentional", "complements"],
        "gap": "판정이 '직무'를 관문으로 쓰는데 산업 사업 52건 중 직무가 잡힌 것은 35%뿐이다. "
               "시설·R&D·판로 사업은 직무가 없어 판정 대상에서 빠진다",
    },
    "정책 실효성 저하": {
        "covered": "partial",
        "module": "산업 태세 판정 — 수요를 덮는가 / 만들 근거가 있는가",
        "finding_keys": ["gaps"],
        "gap": "수요 대조가 직무 축으로만 되어 있어, 기술·판로·금융·시설 수요는 대조되지 않는다",
    },
    "지역 간 격차 심화": {
        "covered": "none",
        "module": None,
        "finding_keys": [],
        "gap": "C8이 군구별 정규화를 해놨으나 신설 4개 구(검단·서해·영종·제물포)의 인구통계가 "
               "없어 정규화가 막혔고, C8 자체가 청년정책 범위라 6대 산업으로는 다시 계산해야 한다",
    },
    "인재 유출과 일자리 미스매치": {
        "covered": "partial",
        "module": "직무별 수요-사업 대조 (일자리 파이프라인 6단계)",
        "finding_keys": ["gaps"],
        "gap": "C가 조건부 보류로 둔 축이다 — 워크넷·NCS API가 차단돼 직종 축 실데이터가 없어 "
               "수요신호 5건 중 2건이 가상 표본이다",
    },
    "기업의 정책 신뢰도 저하": {
        "covered": "none",
        "module": None,
        "finding_keys": [],
        "gap": "C가 '정의 자체가 애매하다'며 별도 조사로 뺐다 — 의회의 사업 타당성 의문은 "
               "기업 신뢰도와 다르다",
    },
    "기업 경쟁력 약화": {
        "covered": "none",
        "module": None,
        "finding_keys": [],
        "gap": "C가 장기 결과로 제외했다 — 기업 단위 매출·고용·수출 데이터가 없어 정답 판정이 "
               "불가능하다",
    },
}

COVER_LABEL = {"full": "판정함", "partial": "일부만", "none": "판정 못 함"}


def axes():
    """C1 원본 순위대로 축 목록을 돌려준다. C1에 없는 축은 만들지 않는다."""
    out = []
    for r in _rows("C1_outcome_feasibility_matrix.csv"):
        name = (r.get("outcome") or "").strip()
        b = AXIS_BINDING.get(name)
        if b is None:  # C1이 축을 늘리면 여기 걸린다 — 조용히 빠지지 않게 표시한다
            b = {"covered": "none", "module": None, "finding_keys": [],
                 "gap": "C1에 새로 생긴 축이다 — 앱에 연결이 아직 없다"}
        out.append({
            "rank": (r.get("rank") or "").strip(),
            "outcome": name,
            "score": (r.get("weighted_score_v3(6대산업)") or "").strip(),
            "c_status": (r.get("mvp_status") or "").strip(),
            **b,
        })
    return out


def counts_for(axis, findings):
    """축 하나에 걸린 판정 건수. 화면에 '몇 건 잡혔나'를 붙이는 데 쓴다."""
    return sum(len(findings.get(k) or []) for k in axis["finding_keys"])


def coverage_summary():
    """7축 중 몇 개를 판정하는가 — 발표에서 정직하게 밝힐 한 줄."""
    a = axes()
    n = len(a)
    part = sum(1 for x in a if x["covered"] == "partial")
    full = sum(1 for x in a if x["covered"] == "full")
    return {"total": n, "full": full, "partial": part, "none": n - full - part}
