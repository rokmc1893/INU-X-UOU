"""빈칸의 뜻을 가르는 규칙 — 「모름」이 「괜찮음」으로 둔갑하지 않게."""
import fit  # noqa: F401
from fit import empty, load, needs
from scenario import intake


def _c(pid, ind="미래차", occ=None, stage=None, it=None):
    return {"policy_id": pid, "strategic_industry": ind, "occupation": occ,
            "stage": stage, "intervention_type": it, "name": pid}


def test_네_가지_뜻이_ok와_unknown으로_갈린다():
    assert empty.MEANING[empty.NONE_TO_PAIR] == "ok"
    assert empty.MEANING[empty.CHECKED_CLEAN] == "ok"
    assert empty.MEANING[empty.NOT_YET] == "unknown"
    assert empty.MEANING[empty.UNREADABLE] == "unknown"


def test_짝이_없으면_문제없음():
    """사업이 하나뿐이면 겹칠 수가 없다 — 이건 흠이 아니다."""
    t = _c("A")
    r = empty.overlaps(t, [t], found=[])
    assert r["kind"] == empty.NONE_TO_PAIR and r["meaning"] == "ok"


def test_직무를_못_읽었으면_모름():
    """상대가 있는데 대상이 안 적혀 있으면 '겹치지 않는다'가 아니라 '모른다'다."""
    t = _c("A", occ=["전직무"])
    r = empty.overlaps(t, [t, _c("B"), _c("C")], found=[])
    assert r["kind"] == empty.UNREADABLE and r["meaning"] == "unknown"
    assert "2건" in r["why"] and r["fix"]


def test_다_맞춰_봤는데_없으면_문제없음():
    t = _c("A", occ=["전직무"])
    r = empty.overlaps(t, [t, _c("B", occ=["전직무"])], found=[])
    assert r["kind"] == empty.CHECKED_CLEAN and r["meaning"] == "ok"


def test_내용이_있으면_빈칸_설명을_내지_않는다():
    assert empty.overlaps(_c("A"), [_c("A"), _c("B")], found=[{"items": ["A", "B"]}]) is None
    assert empty.budget({}, {"status": "RESOLVED"}) is None


def test_예산_미대조는_예산_없음이_아니다():
    r = empty.budget(_c("A"), None)
    assert r["meaning"] == "unknown"
    assert "10건" in r["why"]


def test_수요자료가_없는_것과_수요가_아닌_것을_가른다():
    none = empty.needs_table("항공", [], [])
    assert none["kind"] == empty.NOT_YET
    only_context = empty.needs_table("항공", [{"x": 1}, {"x": 2}], [])
    assert only_context["kind"] == empty.UNREADABLE


def test_실데이터_미래차의_빈칸_이유가_실제와_맞는다():
    """미래차는 사업이 2건 더 있는데 대상이 안 적혀서 대조가 안 된다."""
    cards = load.cards()
    works = [c for c in cards if not load.is_plan(c)]
    t = [c for c in cards if c["policy_id"] == "IC-CAR-001"][0]
    same = [c for c in works if "미래차" in (c.get("strategic_industry") or "")]
    r = empty.overlaps(t, same, found=[])
    assert r["kind"] == empty.UNREADABLE, "미래차 겹침 0건의 이유가 바뀌었다"


def test_올린_자료는_원장과_구분된다():
    card, note = intake._finish({"policy_id": "UP-TXT-001", "name": "시험"}, "붙여넣은 글", "n")
    assert card["data_type"] == intake.UPLOADED
    assert card["evidence_status"] == "UPLOADED_UNVERIFIED"


def test_짧은_글은_받지_않는다():
    try:
        intake.from_text("너무 짧음")
    except intake.IntakeError as e:
        assert "짧" in str(e)
    else:
        raise AssertionError("짧은 글이 통과했다")


def test_주소_형식을_확인한다():
    try:
        intake.from_url("incheon.go.kr")
    except intake.IntakeError as e:
        assert "http" in str(e)
    else:
        raise AssertionError("형식 확인이 안 됐다")
