"""화면의 뼈대 — 조사자 C의 C1 성과축 7개.

축은 우리가 짓지 않는다. `C1_outcome_feasibility_matrix.csv`를 그대로 읽는다. 축마다
**무엇으로 판정하는지 / 못 하면 왜 못 하는지**를 붙이되, 없는 것을 있다고 하지 않는다.

C가 1·2순위로 꼽은 것은 예산 비효율과 산업 생태계이고, 일자리는 5순위 조건부 보류다.
확정본은 그 순서를 그대로 따른다.
"""
from engine.refdata import _rows

BINDING = {
    "정책 예산의 비효율적 사용": dict(
        key="budget", covered="partial",
        module="공식 예산 장부와 맞춰 보기 — 금액·담당 과가 맞는지",
        gap="조사자 C가 대조를 마친 사업이 10건뿐이다. 나머지는 '예산이 없다'가 아니라 "
            "'아직 대조하지 못했다'로 남는다."),
    "산업 생태계 형성 어려움": dict(
        key="ecosystem", covered="partial",
        module="사업 간 사업끼리 겹치거나 끊긴 곳 찾기",
        gap="같은 산업 안의 쌍만 쓴다. 산업이 다른 쌍은 접어 뒀다 — 실제 부서 협의로 "
            "이어지지 않기 때문이다."),
    "정책 실효성 저하": dict(
        key="fit", covered="partial",
        module="기업이 필요하다고 한 것과 사업이 해주는 것을 맞춰 보기",
        gap="원문에 주는 것(수단)이 안 적힌 사업은 어떤 수요와도 맞출 수 없다 — 건수는 "
            "화면 3에 실측으로 표시한다. '해주는 사업이 없다'와 '수단을 못 읽었다'는 다르다."),
    "지역 간 격차 심화": dict(
        key="region", covered="none", module=None,
        gap="C8이 군구별 정규화를 해뒀으나 신설 4개 구(검단·서해·영종·제물포)의 인구통계가 "
            "없어 막혔고, C8 자체가 청년정책 범위라 6대 산업으로는 다시 계산해야 한다."),
    "인재 유출과 일자리 미스매치": dict(
        key="jobs", covered="partial",
        module="직무별로 필요한 사람과 사업 맞춰 보기",
        gap="C가 조건부 보류로 둔 축이다. 워크넷·NCS API가 차단돼 직종 축 실데이터가 없고, "
            "직무 수요신호 5건 중 2건이 가상 표본이다."),
    "기업의 정책 신뢰도 저하": dict(
        key="trust", covered="none", module=None,
        gap="C가 '정의 자체가 애매하다'며 별도 조사로 뺐다 — 의회의 사업 타당성 의문은 "
            "기업 신뢰도와 다르다."),
    "기업 경쟁력 약화": dict(
        key="competitiveness", covered="none", module=None,
        gap="C가 장기 결과로 제외했다 — 기업 단위 매출·고용·수출 데이터가 없어 정답 판정이 "
            "불가능하다."),
}

LABEL = {"full": "판정함", "partial": "일부만", "none": "판정 못 함"}


def all_axes():
    out = []
    for r in _rows("C1_outcome_feasibility_matrix.csv"):
        name = (r.get("outcome") or "").strip()
        b = BINDING.get(name) or dict(
            key=None, covered="none", module=None,
            gap="C1에 새로 생긴 축이다 — 확정본에 연결이 아직 없다.")
        out.append(dict(
            rank=(r.get("rank") or "").strip(), outcome=name,
            score=(r.get("weighted_score_v3(6대산업)") or "").strip(),
            c_status=(r.get("mvp_status") or "").strip(), **b))
    return out


def by_key(key):
    return next((a for a in all_axes() if a["key"] == key), None)


def coverage_line():
    a = all_axes()
    part = sum(1 for x in a if x["covered"] == "partial")
    return dict(total=len(a), partial=part,
                none=sum(1 for x in a if x["covered"] == "none"))
