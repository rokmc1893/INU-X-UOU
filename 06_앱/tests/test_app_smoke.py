"""데모 진입점 스모크 테스트.

app.py는 Streamlit 런타임이 필요해 import할 수 없지만, **문법 오류로 기동 불능이 되는 것**은
테스트로 잡을 수 있다. 실제로 2026-08-13 저녁 app.py가 문법 오류로 18분간 죽어 있었는데
당시 30건 스위트가 전부 통과했다 — 그 사각지대를 닫는다.
"""
import ast
from pathlib import Path

APP = Path(__file__).resolve().parent.parent / "app.py"


def _tree():
    return ast.parse(APP.read_text(encoding="utf-8"))


def test_app_parses():
    """app.py가 파싱된다 = Streamlit이 기동은 한다."""
    assert _tree() is not None


def test_app_defines_demo_entry_points():
    """데모 대본이 의존하는 함수가 실제로 정의돼 있다."""
    names = {n.name for n in ast.walk(_tree()) if isinstance(n, ast.FunctionDef)}
    for fn in ("draft_report", "consult_lines", "a3_reviewers", "chain_html", "_findings_for"):
        assert fn in names, f"{fn}이 app.py에 없다"


def test_app_has_no_hardcoded_contacts():
    """부서 연락처는 A1 레지스트리(refdata)가 단일 출처여야 한다."""
    src = APP.read_text(encoding="utf-8")
    assert "DEPT_CONTACT" not in src
    assert "refdata" in src


def test_next_action_covers_all_five_judgments():
    """판정 5종 전부에 '다음 행동'이 정의돼 있다."""
    src = APP.read_text(encoding="utf-8")
    for key in ("gap", "handoff_break", "overlap_harmful", "overlap_intent", "complement"):
        assert f'"{key}"' in src, f"NEXT_ACTION에 {key}가 없다"
