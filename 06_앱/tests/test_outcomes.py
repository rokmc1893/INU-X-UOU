"""C1의 7개 성과축을 화면 뼈대로 쓰는 부분 검증.

이 앱은 한동안 일자리 파이프라인 한 축으로만 판정했다. C1에서 일자리는 5순위 하나이고
1·2순위는 예산 비효율과 산업 생태계다. 축이 조용히 빠지거나 이름이 바뀌는 것을 막는다.
"""
from engine import outcomes
from engine.detect import run_rules, build_edges, _same_industry


def test_축은_C1_원본을_그대로_읽는다():
    ax = outcomes.axes()
    assert len(ax) == 7, "C1의 축 개수가 바뀌었다 — 화면 설명도 같이 고쳐야 한다"
    assert [a["rank"] for a in ax] == list("1234567"), "C1 순위대로 나와야 한다"
    assert ax[0]["outcome"] == "정책 예산의 비효율적 사용"
    assert ax[4]["outcome"] == "인재 유출과 일자리 미스매치"


def test_모든_축에_판정수단이나_이유가_붙어있다():
    """판정 못 하는 축을 빈칸으로 두면 '문제가 없다'로 읽힌다."""
    for a in outcomes.axes():
        assert a["gap"], f"{a['outcome']}에 한계 설명이 없다"
        if a["covered"] == "none":
            assert a["module"] is None
        else:
            assert a["module"], f"{a['outcome']}에 판정 모듈이 없다"


def test_일자리축이_유일한_축이_아니다():
    """회귀 방지 — 일자리 말고도 판정하는 축이 있어야 한다."""
    covered = [a["outcome"] for a in outcomes.axes() if a["covered"] != "none"]
    assert len(covered) >= 3
    assert any("예산" in c for c in covered), "C 1순위(예산 비효율)가 빠졌다"
    assert any("생태계" in c for c in covered), "C 2순위(산업 생태계)가 빠졌다"


def test_커버리지_요약이_실제와_맞는다():
    s = outcomes.coverage_summary()
    assert s["total"] == 7
    assert s["full"] + s["partial"] + s["none"] == 7


# ── 교차산업 노이즈 ──────────────────────────────────────────
def _c(pid, ind, stage):
    return {"policy_id": pid, "strategic_industry": ind, "stage": stage,
            "occupation": ["전직무"], "target": {}}


def test_산업이_다르면_같은산업_아님으로_표시된다():
    assert _same_industry(_c("A", "바이오", "교육훈련"), _c("B", "항공", "매칭")) is False
    assert _same_industry(_c("A", "바이오", "교육훈련"), _c("B", "바이오", "매칭")) is True


def test_공통과_미상은_어느_산업과도_짝이_된다():
    """전략산업 총괄 계획('공통')과 산업 미상 사업을 노이즈로 잘라내면 안 된다."""
    assert _same_industry(_c("A", "공통", "교육훈련"), _c("B", "항공", "매칭")) is True
    assert _same_industry(_c("A", "", "교육훈련"), _c("B", "항공", "매칭")) is True


def test_복합산업은_부분일치로_본다():
    """B_README: strategic_industry를 배타적 분류로 쓰지 마라 — 양자는 바이오·디지털에 걸친다."""
    assert _same_industry(_c("A", "바이오+디지털데이터", "교육훈련"),
                          _c("B", "디지털데이터", "매칭")) is True


def test_판정결과에_산업일치_표시가_붙는다():
    cards = [_c("A", "바이오", "교육훈련"), _c("B", "항공", "매칭")]
    res = run_rules(cards, [], build_edges(cards, [], None))
    assert res["handoff_breaks"], "인계 공백이 잡혀야 한다"
    assert res["handoff_breaks"][0]["same_industry"] is False
