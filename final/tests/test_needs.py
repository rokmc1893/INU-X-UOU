"""지원 유형 축 — 직무 하나로만 맞추던 것을 7가지로 넓힌 부분의 검증."""
import fit  # noqa: F401
from fit import needs, axes, load


def test_수요유형_분류():
    assert needs.need_of_signal("인력-질적미스매치") == "인력"
    assert needs.need_of_signal("산업구조-밸류체인 결손") == "공급망"
    assert needs.need_of_signal("시설-공급과잉 위험") == "시설"
    assert needs.need_of_signal("금융") == "금융"
    assert needs.need_of_signal("기술-공정도입") == "기술"


def test_수요가_아닌_행은_수요로_세지_않는다():
    """'크다'를 '모자란다'로 바꿔 읽으면 공백 판정이 통째로 틀린다."""
    for pt in ("산업규모(맥락지표)", "인력-모수", "수요부재-전환 미준비",
               "수요신호 부재(역방향 근거)", "고용 감소-역방향 신호"):
        assert needs.need_of_signal(pt) is None, f"'{pt}'이 수요로 샜다"


def test_수단이_없으면_추측하지_않는다():
    assert needs.needs_covered_by({"intervention_type": None}) == []
    assert needs.needs_covered_by({"intervention_type": "시설·인프라"}) == ["시설"]
    assert set(needs.needs_covered_by({"intervention_type": "상담·컨설팅"})) == {"기술", "판로"}


def test_행정신호는_공백이_아니라_행정과제():
    """집행지연을 '덮는 사업 없음'으로 세면 잘못된 경보가 된다."""
    rows = [{"signal_id": "D-1", "strategic_industry": "로봇", "problem_type": "집행지연"}]
    assert needs.coverage([], rows)[0]["verdict"] == "admin_task"


def test_같은_산업_같은_유형이어야_덮는다():
    card = {"policy_id": "P1", "strategic_industry": "바이오",
            "intervention_type": "시설·인프라"}
    same = [{"signal_id": "D-1", "strategic_industry": "바이오", "problem_type": "시설-공급"}]
    other = [{"signal_id": "D-2", "strategic_industry": "항공", "problem_type": "시설-공급"}]
    assert needs.coverage([card], same)[0]["covers"] == ["P1"]
    assert needs.coverage([card], other)[0]["covers"] == []
    assert needs.coverage([card], other)[0]["generic"] == 1


def test_공통산업은_어느_수요와도_짝이_된다():
    card = {"policy_id": "P1", "strategic_industry": "공통", "intervention_type": "교육훈련"}
    rows = [{"signal_id": "D-1", "strategic_industry": "항공", "problem_type": "인력"}]
    assert needs.coverage([card], rows)[0]["covers"] == ["P1"]


def test_실데이터로_인력축만_보던_상태에서_넓어졌다():
    """회귀 방지 — 대조되는 수요가 인력 하나에 몰려 있으면 축 확장이 되돌아간 것이다."""
    cards = load.cards()
    cov = needs.coverage(cards, load.b2())
    kinds = {c["need"] for c in cov if c["verdict"] in ("covered", "uncovered")}
    assert len(kinds) >= 4, f"대조되는 지원 유형이 {kinds}뿐이다"
    assert "공급망" in kinds and "시설" in kinds


def test_축은_C1을_그대로_읽는다():
    ax = axes.all_axes()
    assert len(ax) == 7
    assert ax[0]["outcome"] == "정책 예산의 비효율적 사용"
    assert all(a["gap"] for a in ax), "한계 설명이 빈 축이 있다"


def test_사업명을_못읽은_카드를_지우지_않는다():
    cards = load.cards()
    named = [c for c in cards if c.get("_name_missing")]
    assert all(c["name"] for c in cards), "이름이 빈 카드가 남아 있다"
    assert all("미확인" in c["name"] for c in named)


def test_산업미상_사업은_산업수요를_덮지_않는다():
    """실제 오탐 — 청년일자리 사업 「대학일자리플러스센터」가 바이오 금융 수요를 덮는다고 나왔다.

    비어 있는 것은 '모든 산업'이 아니라 '모른다'다.
    """
    card = {"policy_id": "P1", "intervention_type": "기업보조금"}  # strategic_industry 없음
    rows = [{"signal_id": "D-1", "strategic_industry": "바이오", "problem_type": "금융"}]
    r = needs.coverage([card], rows)[0]
    assert r["covers"] == [], "산업 미상 사업이 산업 수요를 덮는다고 나왔다"
    assert r["verdict"] == "uncovered"


def test_공통은_명시적_전산업이라_덮는다():
    card = {"policy_id": "P1", "strategic_industry": "공통", "intervention_type": "기업보조금"}
    rows = [{"signal_id": "D-1", "strategic_industry": "바이오", "problem_type": "금융"}]
    assert needs.coverage([card], rows)[0]["covers"] == ["P1"]


def test_공백은_금융과_공급망에_몰려있다():
    """확정 결론의 근거 — 이게 흔들리면 발표 결론도 바뀐다."""
    cards = load.cards()
    unc = [c for c in needs.coverage(cards, load.b2()) if c["verdict"] == "uncovered"]
    assert unc, "공백이 하나도 없으면 판정이 무력해진 것이다"
    assert {c["need"] for c in unc} <= {"금융", "공급망"}, \
        f"공백 유형이 바뀌었다: {sorted({c['need'] for c in unc})}"
