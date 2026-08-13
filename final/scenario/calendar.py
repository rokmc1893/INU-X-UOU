"""A2 결정 달력 6트랙 — 공무원이 들어오는 경로와 마감.

트랙마다 필요 문서가 다르다. **유사·중복 검토서가 필수인 트랙은 「다음 연도 본예산
신규사업」 하나**이고, 「기존사업 개편/확대」는 성과평가서가 필수다(A2 원문).

날짜를 지어내지 않는다. 트랙 1만 의회 일자가 구체적이고(제출 11/04 → 의결 12/15)
나머지는 월 단위다.
"""
import re

from engine.refdata import _rows

SOURCE = "조사자 A · A2_decision_calendar.csv (6트랙 전부 CONFIRMED)"

NEW_TRACK = "다음 연도 본예산 신규사업"
RENEW_TRACK = "기존사업 개편/확대"

# 우리가 대신 만들어 주는 문서 — 트랙별로 다르다
OUR_DOC = {
    NEW_TRACK: "유사·중복 검토서",
    # 우리 산출물은 개편안 그 자체가 아니라 **그 근거**다. 이름은 A2 원문을 따른다.
    RENEW_TRACK: "피드백 반영 개편안",
}

_MD = re.compile(r"(\d{1,2})월\s*(\d{1,2})일")


def tracks():
    return _rows("A2_decision_calendar.csv")


def track(name):
    return next((t for t in tracks() if t["decision_type"] == name), None)


def _window(text):
    """'04월 01일 ~ 05월 31일' → ((4,1),(5,31)). 월 단위·수시는 None."""
    found = _MD.findall(text or "")
    if len(found) < 2:
        return None
    (m1, d1), (m2, d2) = found[0], found[1]
    return (int(m1), int(d1)), (int(m2), int(d2))


def _in_window(win, today):
    (m1, d1), (m2, d2) = win
    return (m1, d1) <= (today[0], today[1]) <= (m2, d2)


def open_windows(today):
    """오늘 기준 착수 창구가 열려 있는 트랙. today는 (월, 일).

    '수시/연중'처럼 창구가 항상 열린 트랙은 always=True로 표시한다.
    """
    out = []
    for t in tracks():
        text = t["practical_start_window"]
        if "수시" in text or "연중" in text:
            out.append(dict(track=t, always=True))
            continue
        win = _window(text)
        if win and _in_window(win, today):
            out.append(dict(track=t, always=False))
    return out


def upcoming(today, within_months=2):
    """아직 안 열렸지만 곧 열리는 트랙 — '지금 준비하면 된다'를 안내한다."""
    out = []
    for t in tracks():
        win = _window(t["practical_start_window"])
        if not win:
            continue
        (m1, d1), _ = win
        gap = (m1 - today[0]) % 12
        if 0 < gap <= within_months:
            out.append(dict(track=t, opens=f"{m1}월 {d1}일", months_away=gap))
    return sorted(out, key=lambda x: x["months_away"])


def required_docs(name):
    """그 트랙에 내야 하는 문서. 우리가 대신 만드는 것에 표시를 단다."""
    t = track(name)
    if not t:
        return []
    ours = OUR_DOC.get(name)
    out = []
    for d in re.split(r"[·,]", t["required_input"]):
        d = d.strip()
        if d:
            out.append(dict(doc=d, ours=bool(ours and ours.replace(" ", "") in d.replace(" ", ""))))
    return out


def unknowns():
    return [
        "「개편 시 유사·중복 검토를 생략한다」는 서술은 A 자료 어디에도 없습니다 — "
        "A2 개편 트랙의 필수문서에 안 적혀 있을 뿐입니다.",
        "의회 일자가 구체적인 것은 본예산 신규 트랙뿐입니다(제출 11/04 → 의결 12/15).",
    ]
