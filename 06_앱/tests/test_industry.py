"""산업 태세 — 원칙 '현재 산업은 정책이 맞춰주고, 미래 산업은 정책이 유도한다'의 구현 검증."""
from engine import industry, refdata
from engine.detect import run_rules


def _row(ind, trend, grade, sid="D-999"):
    return {"signal_id": sid, "strategic_industry": ind,
            "sustained_or_spike": trend, "evidence_grade": grade}


def test_실측수요가_있으면_대응형():
    p = industry.posture("바이오", [_row("바이오", "SUSTAINED", "B")])
    assert p["posture"] == industry.RESPONSIVE
    assert "덮는가" in p["question"]


def test_단발이거나_언론근거뿐이면_유도형():
    """SPIKE(단발)나 C등급(언론 정성서술)은 실측 수요로 치지 않는다."""
    for trend, grade in [("SPIKE", "A"), ("SUSTAINED", "C"), ("POLICY_TREND", "A"),
                         ("FORECAST", "B")]:
        p = industry.posture("로봇", [_row("로봇", trend, grade)])
        assert p["posture"] == industry.INDUCING, f"{trend}/{grade}이 대응형으로 샜다"
        assert "만들 근거" in p["question"]


def test_신호가_아예_없으면_판단보류():
    """'수요 없음'과 '조사 없음'은 다르다 — 자료 없음을 수요 없음으로 치환하지 않는다."""
    p = industry.posture("미래차", [])
    assert p["posture"] == industry.UNDECIDED
    assert "조사" in p["question"]


def test_복합산업_신호가_양쪽에_잡힌다():
    rows = [_row("바이오+디지털데이터", "SUSTAINED", "A")]
    assert industry.posture("바이오", rows)["posture"] == industry.RESPONSIVE
    assert industry.posture("디지털데이터", rows)["posture"] == industry.RESPONSIVE


def test_공통신호는_특정산업에_귀속되지_않는다():
    """시도 단위 '공통' 신호로 개별 산업을 대응형으로 승격시키면 안 된다."""
    rows = [_row("공통", "SUSTAINED", "A")]
    assert industry.posture("항공", rows)["posture"] == industry.UNDECIDED


def test_공백문구가_태세에_따라_갈린다():
    """같은 '덮는 사업 없음'이라도 대응형은 대응 실패, 유도형은 정상일 수 있다."""
    demands = [{"signal_id": "D1", "occupation": "바이오생산"}]
    r_ind = run_rules([], demands, [], posture_of=lambda d: "유도형")
    r_res = run_rules([], demands, [], posture_of=lambda d: "대응형")
    assert "흠이 아니" in r_ind["gaps"][0]["reason"]
    assert "이미 확인된 수요" in r_res["gaps"][0]["reason"]
    assert r_ind["gaps"][0]["posture"] == "유도형"


def test_태세_없이도_기존대로_동작():
    demands = [{"signal_id": "D1", "occupation": "바이오생산"}]
    assert run_rules([], demands, [])["gaps"][0]["posture"] is None


def test_통제어휘_밖_산업신호가_되살아난다():
    """로봇·항공·미래차 신호가 직무 어휘 부재로 화면에서 사라졌던 회귀를 막는다."""
    sigs = refdata.industry_signals()
    covered = {i for s in sigs for i in s["industries"]}
    for ind in ("로봇", "항공", "미래차"):
        assert ind in covered, f"{ind} 신호가 또 필터에 걸려 사라졌다"


def test_유도형_근거3종은_없는것을_있다고_하지_않는다():
    card = {"name": "양자컴퓨팅 실증센터", "summary": "", "output_kpi": None}
    ev = industry.inducement_evidence(card, plans=[])
    assert [e["ok"] for e in ev] == [False, False, False]
    assert all(e["detail"] for e in ev), "근거가 없으면 왜 없는지 적어야 한다"
