"""A3 3단계 산출물 초안 — 담당자가 결재문서에 붙여 쓴다.

문서 이름은 A3·A2 원문을 따른다. 신규 트랙이면 「유사·중복 사업 자체 검토서」,
개편 트랙이면 「피드백 반영 개편안」의 근거 부분이다.

**이 도구는 정책을 제안하지 않는다.** 발의권은 A1상 과(課) 단위이고 1단계 성립 결정은
담당 과장이다. 우리는 검토서 초안과 근거만 낸다.

**모든 판정은 '후보'로 적는다.** 조사자 C의 실패기준:
  "역할중첩 후보를 '확정'으로 표시하는 화면 요소가 하나라도 발견되면 즉시 되돌린다."
"""
from fit import needs as _needs

from . import actors, calendar, workflow

DISCLAIMER = ("이 문서는 초안입니다. 아래 판정은 전부 **후보**이며, 확정은 부서 협의로 합니다. "
              "판정에 AI는 관여하지 않았습니다 — 원문에서 항목을 뽑는 데만 쓰고 "
              "고르는 일은 규칙이 했습니다.")


def _bullet(items):
    return "\n".join(f"- {i}" for i in items) if items else "- (해당 없음)"


def _kinds(rows):
    """빈칸의 종류를 겹치지 않게, 나온 차례대로."""
    out = []
    for c in rows:
        p = _needs.plain(c["need"])
        if p not in out:
            out.append(p)
    return out


def _hints(rows):
    """머리줄에 쓴 칸 이름이 무엇을 세는지 바로 밑에 푼다.

    항목과 같은 높이에 두면 자료 하나로 잘못 읽힌다. 들여쓴 괄호 줄로 둔다.
    """
    seen, out = set(), []
    for c in rows:
        if c["need"] not in seen:
            seen.add(c["need"])
            out.append(f"  ({_needs.plain(c['need'])} = {_needs.HINT[c['need']]})")
    return "\n".join(out)


def _sub(items):
    """머리줄에 딸린 항목 — 한 단 들여쓴다."""
    return "\n".join(f"  - {i}" for i in items) if items else "  - (해당 없음)"


def _link(name, url):
    """검토서에도 원문 링크를 넣는다 — 결재선에서 눌러 확인할 수 있어야 한다."""
    return f"[{name}]({url})" if url and str(url).startswith("http") else f"{name} (원문 주소 없음)"


def draft(card, findings, coverage, track_name, today, name_of=lambda p: p, url_of=lambda p: None):
    """검토서 초안을 마크다운으로 돌려준다.

    card       : 검토 대상 사업 카드
    findings   : detect.run_rules + budget_findings 결과
    coverage   : fit.needs.coverage() 결과 중 이 사업의 산업에 해당하는 것
    track_name : A2 트랙 이름
    today      : (월, 일)
    """
    pid = card["policy_id"]
    ind = (card.get("strategic_industry") or "미상").strip()
    tr = calendar.track(track_name) or {}
    st = workflow.our_stage()

    def mine(key):
        return [f for f in (findings.get(key) or [])
                if pid in f.get("items", []) and f.get("same_industry", True)]

    oh, oi, cp = mine("overlaps_harmful"), mine("overlaps_intentional"), mine("complements")
    hb = mine("handoff_breaks")
    uncovered = [c for c in coverage if c["verdict"] == "uncovered"]
    thin = [c for c in coverage if c["verdict"] == "covered" and len(c["covers"]) == 1]

    def pair(f):
        a, b = f["items"]
        other = b if a == pid else a
        return f"{_link(name_of(other), url_of(other))} — {f['reason']}"

    lines = [
        f"# {tr.get('decision_type', track_name)} — 검토서 초안",
        "",
        f"> {DISCLAIMER}",
        "",
        f"- 검토 대상 사업: **{card.get('name') or pid}** (`{pid}`) "
        f"· {_link('원문', card.get('source_url'))}",
        f"- 전략산업: {ind} · 소관(사업 문서 기준): {card.get('owner_dept') or '미확인'}",
        f"- 행정 절차상 위치: A3 {st['no']}단계 「{st['name']}」",
        f"- 작성 기준일: 2026-{today[0]:02d}-{today[1]:02d}",
        "",
        "## 1. 이 검토의 근거",
        "",
        f"A3 {st['no']}단계의 반려 사유는 「{workflow.duplicate_test_source()}」입니다.",
        "이 검토서는 그 세 가지(대상·수단·직무)를 기존 사업과 대조한 결과입니다.",
        "",
        "## 2. 확인 결과 (전부 후보입니다)",
        "",
        f"### 2-1. 중복 — {len(oh)}건 (받는 사람·주는 것·직무가 모두 같음)",
        _bullet([pair(f) for f in oh]),
        "",
        f"### 2-2. 중복 아님 — 일부러 나란히 둔 것 {len(oi)}건 / 서로 채워 주는 것 {len(cp)}건",
        "",
        "받는 사람이나 주는 것이 달라 중복이 아닙니다. 중복이라는 이유로 잘못 반려당하는 것을",
        "막기 위해 함께 적습니다.",
        "",
        _bullet([pair(f) for f in oi + cp]),
        "",
        f"### 2-3. 연계 끊김 — {len(hb)}쌍 (앞 사업을 마쳐도 뒤 사업으로 이어지지 않음)",
        _bullet([pair(f) for f in hb]),
        "",
        "## 3. 이 산업에 필요한 것을 사업이 해주고 있는가",
        "",
        # 「2건」만 적으면 결재선에서 무엇이 비었는지 알 수 없다. 어느 칸인지 이름을
        # 먼저 밝히고, 그 칸이 무엇을 세는지도 한 줄 붙인다 — 「자금」이 이 사업에 붙은
        # 예산으로 읽히면 「30억이 있는데 왜 비었나」가 된다.
        f"- 해주는 사업이 없는 것: **{len(uncovered)}건** — "
        + (" · ".join(_kinds(uncovered)) if uncovered else "없음"),
        _hints(uncovered),
        _sub([f"{c['problem_type']} — {c['value'][:60]} · "
              f"{_link(c['signal_id'] + ' ' + c['grade'] + '등급', c.get('source_url'))}"
              for c in uncovered]),
        "",
        f"- 해주는 사업이 딱 하나뿐인 것: **{len(thin)}건** (그 사업이 멈추면 바로 공백이 됩니다)"
        + (" — " + " · ".join(_kinds(thin)) if thin else ""),
        _hints(thin),
        _sub([f"{c['problem_type']} ← "
              f"{_link(name_of(c['covers'][0]), url_of(c['covers'][0]))}" for c in thin]),
        "",
        "## 4. 미확인 항목과 그 이유",
        "",
        "비워 두지 않습니다. 못 본 것을 밝히는 칸입니다.",
        "",
        _bullet(
            ["이 사업의 예산 원장 대조: " + (card.get("budget_status")
                or "아직 하지 못했습니다 — 「예산이 없다」는 뜻이 아닙니다")]
            + ([] if card.get("intervention_type")
               else ["이 사업이 「주는 것(수단)」이 원문에 적혀 있지 않아 수요 대조를 하지 못했습니다"])
            + workflow.unknowns() + actors.unknowns()),
        "",
        "## 5. 협의 요청 부서",
        "",
        f"> {actors.CAVEAT}",
        "",
        _bullet([f"**{a['team']}** ({a['bureau']}) — {a['decision_right']} · 연락처 {a['contact']} "
                 f"· {_link('부서 근거', a.get('source_url'))}"
                 for a in actors.consult_for(card)] or ["산업이 확인되지 않아 협의처를 안내하지 못합니다"]),
        "",
        "A3 3단계 검토자:",
        _bullet([f"{r['who']} — {r['why']}" for r in actors.reviewers_for(card)]),
        "",
        "## 6. 다음 창구와 마감",
        "",
        f"- 이 트랙: **{tr.get('decision_type', track_name)}** · "
        f"착수 {tr.get('practical_start_window', '?')} · 마감 {tr.get('formal_deadline', '?')}",
        f"- 심사: {tr.get('review_body', '?')}",
        f"- 이번 창구를 놓치면: {tr.get('next_available_window', '?')}",
        "",
        "필요 문서:",
        _bullet([f"{d['doc']}{' ← 이 도구의 산출물' if d['ours'] else ''}"
                 for d in calendar.required_docs(track_name)]),
        "",
        "지금 열려 있는 창구:",
        _bullet([f"{o['track']['decision_type']}"
                 f"{' (수시)' if o['always'] else ''} · 마감 {o['track']['formal_deadline']}"
                 for o in calendar.open_windows(today)]),
        "",
        "곧 열리는 창구:",
        _bullet([f"{u['track']['decision_type']} — {u['opens']} ({u['months_away']}개월 뒤)"
                 for u in calendar.upcoming(today, 3)]),
        "",
        "---",
        f"출처: {workflow.SOURCE} · {actors.SOURCE} · {calendar.SOURCE}",
    ]
    return "\n".join(lines)
