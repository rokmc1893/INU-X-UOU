"""A2 결정 달력 6트랙 — 공무원이 들어오는 경로.

트랙마다 필요 문서가 다르므로 우리 산출물도 달라져야 한다. **유사중복 검토서가 필수인
트랙은 「다음 연도 본예산 신규사업」 하나**다(A2 원문). 그것이 우리 주 산출물의 자리다.

**주의**: 트랙 1만 의회 일자가 구체적이다(제출 11/04 → 의결 12/15). 나머지는 월 단위라
날짜를 지어내지 않는다.
"""

TRACKS = []  # TODO: A2_decision_calendar.csv 6행을 그대로 옮긴다


def open_windows(today):
    """오늘 기준 착수 창구가 열려 있는 트랙."""
    raise NotImplementedError


def next_window(track, today):
    """이번 창구를 놓쳤을 때 다음 기회. A2 `next_available_window`를 쓴다."""
    raise NotImplementedError


def required_docs(track):
    """그 트랙에 내야 하는 문서. 우리가 대신 만들어 주는 것에 표시를 단다."""
    raise NotImplementedError
