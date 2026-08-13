"""정책핏 인천 — 확정본.

화면 순서는 조사자 C의 성과축 순위(C1)를 그대로 따른다.
  ① 예산이 새는가 (C 1순위)  ② 사업끼리 이어지는가 (C 2순위)
  ③ 산업 수요와 맞는가 (C 3순위)  ④ 조치

여태 이 도구는 일자리 파이프라인 한 축으로만 판정했다. C1에서 일자리는 5순위 조건부
보류이고 1·2순위는 예산 비효율과 산업 생태계다 — 확정본은 그 순서로 다시 짰다.
"""
import html
from pathlib import Path

import streamlit as st

import fit  # noqa: F401  — 06_앱의 engine을 sys.path에 올린다
from fit import axes, load, needs
from engine import industry

BASE = Path(__file__).resolve().parent
TODAY = "2026-08-13"

st.set_page_config(page_title="정책핏 인천 — 확정본", layout="wide")
st.markdown((BASE / "fit" / "_style.txt").read_text(encoding="utf-8"),
            unsafe_allow_html=True)


def esc(x):
    return html.escape(str(x if x is not None else ""))


@st.cache_resource
def prepare():
    cards = load.cards()
    edges, findings, postures = load.build(cards)
    b2 = load.b2()
    return cards, edges, findings, postures, b2, needs.coverage(cards, b2)


cards, edges, findings, POSTURES, B2, COV = prepare()
by_id = {c["policy_id"]: c for c in cards}
plans = [c for c in cards if load.is_plan(c)]
works = [c for c in cards if not load.is_plan(c)]


def name_of(pid):
    return (by_id.get(pid, {}) or {}).get("name") or pid


def badge(kind, text):
    return f'<span class="v {kind}">{esc(text)}</span>'


# ── 사이드바 ────────────────────────────────────────────────
st.sidebar.title("정책핏 인천")
st.sidebar.caption("확정본 · 조사자 C의 성과축 순서")
SCREENS = ["0 무엇을 보는가", "1 예산이 새는가", "2 사업끼리 이어지는가",
           "3 산업 수요와 맞는가", "4 조치 제안"]
screen = st.sidebar.radio("화면", SCREENS, label_visibility="collapsed")
st.sidebar.divider()
_inds = ["전체"] + industry.INDUSTRIES
pick = st.sidebar.selectbox("산업", _inds,
                            help="6대 전략산업. 이 목록의 근거는 화면 0에 밝혀 뒀습니다.")
st.sidebar.caption(f"사업 {len(works)}건 · 계획 {len(plans)}건 · 수요신호 {len(B2)}행")


def in_scope(card):
    if pick == "전체":
        return True
    v = card.get("strategic_industry") or ""
    return pick in v or "공통" in v


def sig_in_scope(row):
    return pick == "전체" or pick in (row.get("industry") or row.get("strategic_industry") or "")


st.markdown(
    f'<div class="doc-head"><span class="t">{esc(screen[2:])}</span>'
    f'<span class="m">정책핏 인천 · 기준일 {TODAY} · 산업 {esc(pick)}</span></div>',
    unsafe_allow_html=True)
_steps = "".join(
    f'<div class="step{" on" if s == screen else ""}">'
    f'<span class="n">{s[0]}</span>{esc(s[2:])}</div>' for s in SCREENS)
st.markdown(f'<div class="steps">{_steps}</div>', unsafe_allow_html=True)


# ═══ 화면 0 — 무엇을 보는가 ═══════════════════════════════
if screen.startswith("0"):
    st.markdown(
        '<p class="small">인천 6대 전략산업의 <b>사업</b>과 <b>산업 수요</b>를 대조해, '
        '어긋난 곳을 후보로 골라냅니다. 확정은 부서 협의로 합니다.</p>',
        unsafe_allow_html=True)

    # 확정 결론 — 화면 3의 실측에서 그대로 끌어온다. 손으로 쓴 숫자를 두지 않는다.
    _real = [c for c in COV if c["verdict"] in ("covered", "uncovered")]
    _unc = [c for c in _real if c["verdict"] == "uncovered"]
    _by_need = {}
    for c in _real:
        d = _by_need.setdefault(c["need"], [0, 0])
        d[0] += 1
        d[1] += (c["verdict"] == "uncovered")
    _gapkinds = sorted({c["need"] for c in _unc})
    _means = {}
    for c in works:
        for n in needs.needs_covered_by(c):
            _means[n] = _means.get(n, 0) + 1
    st.markdown(
        '<div style="border:2px solid var(--ink);padding:.8rem 1rem;margin:.3rem 0 1.2rem">'
        '<div style="font-family:var(--serif);font-size:1.05rem;font-weight:600">'
        f'지금 자료로 내린 결론 — 인천 6대 산업의 공백은 「{"·".join(_gapkinds)}」에 몰려 있습니다'
        '</div><div class="small" style="margin-top:.4rem">'
        f'대조한 산업 수요 {len(_real)}건 중 덮는 사업이 없는 것은 <b>{len(_unc)}건</b>이고, '
        f'그 <b>전부</b>가 {"·".join(_gapkinds)} 수요입니다. '
        + " / ".join(f'{n} {v[0]-v[1]}÷{v[0]} 덮임' for n, v in sorted(_by_need.items()))
        + '<br>반면 사업이 주는 것은 '
        + ", ".join(f"{n} {v}건" for n, v in sorted(_means.items(), key=lambda x: -x[1]))
        + '입니다 — <b>정책이 몰려 있는 곳'
        + f'({"·".join(n for n, _ in sorted(_means.items(), key=lambda x: -x[1])[:2])})과 '
        + f'모자란 곳({"·".join(_gapkinds)})이 다릅니다.</b>'
        '</div></div>', unsafe_allow_html=True)

    st.subheader("세 단어를 구분해서 씁니다")
    st.markdown(
        '<table style="width:100%;border-collapse:collapse;font-size:.85rem">'
        '<tr style="border-top:1px solid var(--rule);border-bottom:1px solid var(--rule)">'
        '<td style="padding:.4rem .6rem;width:4.5rem;font-weight:700;color:var(--harbor)">산업</td>'
        '<td style="padding:.4rem .6rem"><b>필요가 나오는 쪽.</b> 사람·기술·돈·판로·'
        '받쳐 줄 기업·공간이 모자란다고 신호가 나옵니다</td></tr>'
        '<tr style="border-bottom:1px solid var(--rule)">'
        '<td style="padding:.4rem .6rem;font-weight:700;color:var(--harbor)">정책</td>'
        '<td style="padding:.4rem .6rem"><b>방향을 정하는 상위 문서.</b> 기본계획·종합계획·전략. '
        f'예산이 직접 붙지 않아 중복 검토 대상이 아닙니다 — 지금 {len(plans)}건</td></tr>'
        '<tr style="border-bottom:1px solid var(--ink)">'
        '<td style="padding:.4rem .6rem;font-weight:700;color:var(--seal)">사업</td>'
        '<td style="padding:.4rem .6rem"><b>예산이 붙는 실행 단위 — 이 도구가 검토하는 대상.</b> '
        f'지금 {len(works)}건</td></tr></table>', unsafe_allow_html=True)

    st.subheader("산업과 정책이 어긋나면 생기는 일 — 7가지 중 어디까지 봅니까")
    rows = ['<table style="width:100%;border-collapse:collapse;font-size:.82rem">'
            '<tr style="border-bottom:1.5px solid var(--ink)">'
            '<th style="text-align:left;padding:.4rem .4rem;width:1.4rem"></th>'
            '<th style="text-align:left;padding:.4rem .5rem">생기는 문제</th>'
            '<th style="text-align:left;padding:.4rem .5rem;width:5rem">이 도구는</th>'
            '<th style="text-align:left;padding:.4rem .5rem">무엇으로 / 왜 못 하는지</th></tr>']
    for a in axes.all_axes():
        cl = {"full": "ok", "partial": "warn", "none": "act"}[a["covered"]]
        what = (f'{esc(a["module"])}<br><span class="small">한계: {esc(a["gap"])}</span>'
                if a["module"] else f'<span class="small">{esc(a["gap"])}</span>')
        rows.append(
            '<tr style="border-bottom:1px solid var(--rule)">'
            f'<td style="padding:.45rem .4rem;color:var(--muted)">{esc(a["rank"])}</td>'
            f'<td style="padding:.45rem .5rem;font-weight:700">{esc(a["outcome"])}'
            f'<br><span class="small">조사자 C · {esc(a["c_status"])}</span></td>'
            f'<td style="padding:.45rem .5rem">{badge(cl, axes.LABEL[a["covered"]])}</td>'
            f'<td style="padding:.45rem .5rem">{what}</td></tr>')
    st.markdown("".join(rows) + "</table>", unsafe_allow_html=True)
    cl = axes.coverage_line()
    st.markdown(
        f'<p class="small">7가지 중 <b>{cl["partial"]}가지를 일부만</b> 판정하고 '
        f'<b>{cl["none"]}가지는 판정하지 못합니다.</b> 못 하는 축도 지우지 않고 이유를 적었습니다 — '
        '자료가 없는 것이지 문제가 없는 것이 아닙니다. 축과 순위는 조사자 C의 '
        '<code>C1_outcome_feasibility_matrix.csv</code>를 그대로 읽었습니다.</p>',
        unsafe_allow_html=True)

    with st.expander("이 6개 산업 목록은 어디서 왔습니까 — 근거 등급"):
        st.markdown(
            '<p class="small"><b>확인된 것</b> — 「인천 전략산업육성 종합계획」(2023 수립, '
            '산업정책과 총괄)이 2015년 <b>8대</b>를 <b>6대</b>로 재편했다고 적혀 있습니다 '
            '(정책원장 <code>IC-COM-001</code>).<br>'
            '<b>확인 못 한 것</b> — 그 종합계획의 <b>원문·고시문을 확보하지 못했습니다.</b> '
            '근거는 언론기사 1건이고 등급은 <code>SECONDARY_PRESS_ONLY</code>입니다. '
            '민선8기 시정운영계획·산업발전 기본계획·지역산업진흥계획은 조사 원장에 없습니다. '
            '발표에서 "인천시가 지정한 6대"라고 단정하지 않습니다.<br>'
            '<b>주의</b> — 조사자 A는 <b>다른 6대</b>를 쓰고 있었습니다(바이오·반도체·미래모빌리티·'
            '로봇항공·물류항만·스마트시티AI). 이쪽은 <b>부서명 기준</b>이라 협의 대상을 찾을 때는 '
            'A의 구분이 더 맞을 수 있습니다.<br>'
            '<b>배타적 분류가 아닙니다</b> — 양자는 바이오와 디지털데이터에 걸쳐 있고, '
            '반도체·바이오는 같은 과 소관이라 예산이 섞여 있습니다.</p>',
            unsafe_allow_html=True)


# ═══ 화면 1 — 예산이 새는가 (C 1순위) ═════════════════════
elif screen.startswith("1"):
    a = axes.by_key("budget")
    st.markdown(f'<p class="small">조사자 C의 <b>{esc(a["c_status"])}</b> · '
                f'타당성 점수 {esc(a["score"])}</p>', unsafe_allow_html=True)
    bc = [x for x in findings["budget_confirmed"] if in_scope(by_id[x["pid"]])]
    bu = [x for x in findings["budget_unverified"] if in_scope(by_id[x["pid"]])]
    bx = [x for x in findings["budget_conflicts"] if in_scope(by_id[x["pid"]])]
    dm = [x for x in findings["dept_mismatch"] if in_scope(by_id[x["pid"]])]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("원장과 일치", f"{len(bc)}건")
    c2.metric("재검토 필요", f"{len(bx)}건")
    c3.metric("소관 불일치", f"{len(dm)}건", help="카드의 소관 부서와 공식 원장이 다릅니다")
    c4.metric("원장에서 못 찾음", f"{len(bu)}건")

    if dm:
        st.subheader("소관 부서가 원장과 다릅니다 — 협의 대상이 바뀝니다")
        st.markdown('<p class="small">공문을 잘못된 과로 보내면 회신이 오지 않습니다. '
                    '아래는 공식 예산 원장 기준으로 고쳐야 할 것들입니다.</p>',
                    unsafe_allow_html=True)
        r = ['<table style="width:100%;border-collapse:collapse;font-size:.85rem">'
             '<tr style="border-bottom:1.5px solid var(--ink)">'
             '<th style="text-align:left;padding:.4rem .5rem">사업</th>'
             '<th style="text-align:left;padding:.4rem .5rem;width:13rem">사업 문서에 적힌 소관</th>'
             '<th style="text-align:left;padding:.4rem .5rem;width:14rem">공식 예산 원장의 소관</th></tr>']
        for x in dm:
            r.append('<tr style="border-bottom:1px solid var(--rule)">'
                     f'<td style="padding:.45rem .5rem">{esc(name_of(x["pid"])[:40])}</td>'
                     f'<td style="padding:.45rem .5rem;color:var(--muted)">{esc(x["card"])}</td>'
                     f'<td style="padding:.45rem .5rem;font-weight:700">{esc(x["official"])}</td></tr>')
        st.markdown("".join(r) + "</table>", unsafe_allow_html=True)

    if bx:
        st.subheader("금액이 어긋납니다")
        for x in bx:
            st.markdown(f'- **{name_of(x["pid"])}** — {esc(x.get("note") or "원장과 대조 필요")}')

    st.subheader("대조가 끝난 사업")
    if bc:
        r = ['<table style="width:100%;border-collapse:collapse;font-size:.85rem">'
             '<tr style="border-bottom:1.5px solid var(--ink)">'
             '<th style="text-align:left;padding:.4rem .5rem">사업</th>'
             '<th style="text-align:left;padding:.4rem .5rem;width:11rem">공식 원장 금액</th>'
             '<th style="text-align:left;padding:.4rem .5rem;width:7rem">매칭</th></tr>']
        for x in bc:
            won = x.get("budget_won")
            r.append('<tr style="border-bottom:1px solid var(--rule)">'
                     f'<td style="padding:.45rem .5rem">{esc(name_of(x["pid"])[:44])}</td>'
                     f'<td style="padding:.45rem .5rem">{f"{won:,}원" if won else "—"}</td>'
                     f'<td style="padding:.45rem .5rem">'
                     f'{badge("na" if x.get("loose") else "ok", "느슨" if x.get("loose") else "정확")}'
                     '</td></tr>')
        st.markdown("".join(r) + "</table>", unsafe_allow_html=True)
    st.markdown(
        f'<p class="small"><b>이 축의 한계</b>: {esc(a["gap"])} '
        f'대조가 끝난 것은 사업 {len(works)}건 중 {len(bc) + len(bu) + len(bx)}건입니다. '
        '나머지는 "예산이 없다"가 아니라 <b>"아직 확인하지 못했다"</b>입니다.</p>',
        unsafe_allow_html=True)


# ═══ 화면 2 — 사업끼리 이어지는가 (C 2순위) ═══════════════
elif screen.startswith("2"):
    a = axes.by_key("ecosystem")
    st.markdown(f'<p class="small">조사자 C의 <b>{esc(a["c_status"])}</b> · '
                f'타당성 점수 {esc(a["score"])}</p>', unsafe_allow_html=True)

    def keep(f):
        return f.get("same_industry", True) and all(in_scope(by_id[p]) for p in f["items"])

    oh = [f for f in findings["overlaps_harmful"] if keep(f)]
    oi = [f for f in findings["overlaps_intentional"] if keep(f)]
    cp = [f for f in findings["complements"] if keep(f)]
    hb = [f for f in findings["handoff_breaks"] if keep(f)]
    hb_cross = [f for f in findings["handoff_breaks"] if not f.get("same_industry", True)]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("조정 필요 중복", f"{len(oh)}건", help="받는 사람·주는 것·직무가 모두 같습니다")
    c2.metric("의도적 병행", f"{len(oi)}건", help="주는 것은 같지만 받는 사람이 다릅니다")
    c3.metric("보완 관계", f"{len(cp)}건", help="주는 것이 달라 중복이 아닙니다")
    c4.metric("인계 끊김", f"{len(hb)}쌍")

    if oh:
        st.subheader("조정이 필요한 중복 후보")
        for f in oh:
            st.markdown(f'- **{name_of(f["items"][0])}** ↔ **{name_of(f["items"][1])}**  \n'
                        f'  <span class="small">{esc(f["reason"])}</span>',
                        unsafe_allow_html=True)
        st.info("→ 두 사업의 소관 부서에 조정 협의를 요청하세요. "
                "**중복 '확정'이 아니라 '후보'입니다** — 확정은 부서 협의로 합니다.")

    if cp:
        st.subheader("중복처럼 보이지만 중복이 아닙니다")
        st.markdown('<p class="small">주는 것이 달라서 겹치지 않습니다. 검토서에 이유를 적어 두면 '
                    '나중에 중복이라는 이유로 잘못 반려당하는 것을 막아 줍니다.</p>',
                    unsafe_allow_html=True)
        for f in cp[:8]:
            st.markdown(f'- {name_of(f["items"][0])} ↔ {name_of(f["items"][1])}  \n'
                        f'  <span class="small">{esc(f["reason"])}</span>',
                        unsafe_allow_html=True)

    st.subheader("인계가 끊긴 구간")
    if hb:
        groups = {}
        for f in hb:
            groups.setdefault(f["reason"], []).append(f["items"])
        for reason, pairs in sorted(groups.items(), key=lambda kv: -len(kv[1])):
            with st.expander(f"{reason} · {len(pairs)}쌍"):
                for p in pairs[:8]:
                    st.markdown(f"- {name_of(p[0])} → {name_of(p[1])}")
                if len(pairs) > 8:
                    st.caption(f"…외 {len(pairs) - 8}쌍")
    else:
        st.success("이 산업 안에서는 인계 끊김 후보가 없습니다")
    if hb_cross:
        st.markdown(
            f'<p class="small">산업이 서로 다른 {len(hb_cross)}쌍은 뺐습니다 — '
            '「청년도약기지」와 「대한항공 MRO 클러스터」 사이에 인계 절차가 없다는 지적은 '
            '실제 부서 협의로 이어지지 않기 때문입니다. 지운 것이 아니라 세어서 밝힙니다.</p>',
            unsafe_allow_html=True)
    st.markdown(f'<p class="small"><b>이 축의 한계</b>: {esc(a["gap"])}</p>',
                unsafe_allow_html=True)


# ═══ 화면 3 — 산업 수요와 맞는가 (C 3순위) ════════════════
elif screen.startswith("3"):
    a = axes.by_key("fit")
    st.markdown(f'<p class="small">조사자 C의 <b>{esc(a["c_status"])}</b> · '
                f'타당성 점수 {esc(a["score"])}</p>', unsafe_allow_html=True)

    st.markdown(
        '<div style="border:1px solid var(--ink);padding:.7rem .9rem;margin:.2rem 0 1rem">'
        f'<b>{industry.PRINCIPLE}</b><br>'
        '<span class="small">그래서 산업마다 물어야 할 질문이 다릅니다. 이미 수요가 있는 '
        '산업엔 "그 수요를 덮었는가"를, 아직 수요가 없는 산업엔 "수요를 만들 근거가 있는가"를 '
        '묻습니다.</span></div>', unsafe_allow_html=True)

    st.subheader("가. 이 산업에 무엇을 물어야 하는가")
    r = ['<table style="width:100%;border-collapse:collapse;font-size:.83rem">'
         '<tr style="border-bottom:1.5px solid var(--ink)">'
         '<th style="text-align:left;padding:.4rem .5rem;width:5.5rem">산업</th>'
         '<th style="text-align:left;padding:.4rem .5rem;width:4.5rem">태세</th>'
         '<th style="text-align:left;padding:.4rem .5rem">물어야 할 질문</th>'
         '<th style="text-align:left;padding:.4rem .5rem">그렇게 본 이유</th></tr>']
    for ind in industry.INDUSTRIES:
        if pick not in ("전체", ind):
            continue
        p = POSTURES[ind]
        r.append('<tr style="border-bottom:1px solid var(--rule)">'
                 f'<td style="padding:.45rem .5rem;font-weight:700">{esc(ind)}</td>'
                 f'<td style="padding:.45rem .5rem">'
                 f'{badge("ok" if p["posture"] == industry.RESPONSIVE else "act", p["posture"])}</td>'
                 f'<td style="padding:.45rem .5rem">{esc(p["question"])}</td>'
                 f'<td style="padding:.45rem .5rem;font-size:.77rem;color:var(--muted)">'
                 f'{esc(p["why"])}</td></tr>')
    st.markdown("".join(r) + "</table>", unsafe_allow_html=True)
    st.markdown('<p class="small">태세는 사람이 정한 것이 아니라 <b>수요신호가 정한 것</b>입니다. '
                '새 조사가 들어오면 태세도 질문도 저절로 바뀝니다.</p>', unsafe_allow_html=True)

    st.subheader("나. 산업이 필요로 하는 것을 사업이 덮는가")
    st.markdown('<p class="small">직무 하나가 아니라 <b>지원 유형 7가지</b>로 맞춥니다 — '
                '사람·기술·돈·판로·받쳐 줄 기업·공간·행정. 예전에는 사람 축만 봤습니다.</p>',
                unsafe_allow_html=True)
    scoped = [c for c in COV if pick == "전체" or pick in c["industry"]]
    real = [c for c in scoped if c["verdict"] in ("covered", "uncovered")]
    unc = [c for c in real if c["verdict"] == "uncovered"]
    thin = [c for c in real if c["verdict"] == "covered" and len(c["covers"]) == 1]

    r = ['<table style="width:100%;border-collapse:collapse;font-size:.83rem">'
         '<tr style="border-bottom:1.5px solid var(--ink)">'
         '<th style="text-align:left;padding:.4rem .5rem;width:6rem">필요한 것</th>'
         '<th style="text-align:left;padding:.4rem .5rem;width:4.5rem">산업</th>'
         '<th style="text-align:left;padding:.4rem .5rem">무엇이 확인됐는가</th>'
         '<th style="text-align:left;padding:.4rem .5rem;width:9rem">덮는 사업</th></tr>']
    for c in sorted(real, key=lambda x: (x["verdict"] != "uncovered", len(x["covers"]))):
        n = len(c["covers"])
        mark = (badge("act", "없음") if n == 0
                else badge("na", "1건뿐") if n == 1 else badge("ok", f"{n}건"))
        if n and n <= 2:
            mark += ('<br><span class="small">'
                     + esc(", ".join(name_of(p)[:18] for p in c["covers"])) + "</span>")
        r.append('<tr style="border-bottom:1px solid var(--rule)">'
                 f'<td style="padding:.45rem .5rem;font-weight:700">{esc(c["need"])}'
                 f'<br><span class="small">{esc(needs.NEED_LABEL[c["need"]])}</span></td>'
                 f'<td style="padding:.45rem .5rem">{esc(c["industry"])}</td>'
                 f'<td style="padding:.45rem .5rem">{esc(c["problem_type"])}'
                 f'<br><span class="small">{esc(c["value"][:52])} · {esc(c["signal_id"])} '
                 f'{esc(c["grade"])}등급 {esc(c["trend"])}</span></td>'
                 f'<td style="padding:.45rem .5rem">{mark}</td></tr>')
    st.markdown("".join(r) + "</table>", unsafe_allow_html=True)

    if unc:
        kinds = sorted({c["need"] for c in unc})
        st.error(f"**덮는 사업이 없는 수요 {len(unc)}건 — 전부 「{', '.join(kinds)}」입니다.** "
                 + " / ".join(f"{c['industry']} {c['signal_id']}" for c in unc))
        for c in unc:
            st.markdown(f'- **{c["industry"]} · {c["problem_type"]}** — {esc(c["value"][:70])}  \n'
                        f'  <span class="small">이 신호의 한계: {esc(c["limit"][:110])}</span>',
                        unsafe_allow_html=True)
    if thin:
        st.warning(f"덮는 사업이 1건뿐인 수요 {len(thin)}건 — 그 사업이 멈추면 바로 공백이 됩니다: "
                   + ", ".join(f"{c['industry']} {c['need']}" for c in thin))

    admin = [c for c in scoped if c["verdict"] == "admin_task"]
    notneed = [c for c in scoped if c["verdict"] == "not_a_need"]
    with st.expander(f"수요로 세지 않은 신호 {len(admin) + len(notneed)}건 — 왜 뺐는지"):
        st.markdown(f'<p class="small"><b>행정 과제 {len(admin)}건</b> — 집행지연·수요조사 노후화·'
                    '데이터 공백처럼 <b>사업으로 덮는 것이 아닌</b> 신호입니다. 공백으로 세면 '
                    '잘못된 경보가 됩니다.<br>'
                    f'<b>수요가 아닌 것 {len(notneed)}건</b> — 산업 규모·현원·"수요가 없다"는 '
                    '역방향 신호입니다. "크다"를 "모자란다"로 바꿔 읽지 않습니다.</p>',
                    unsafe_allow_html=True)
        for c in (admin + notneed)[:14]:
            st.markdown(f'- `{c["signal_id"]}` {c["industry"]} · {esc(c["problem_type"])}')

    um = [c for c in works if in_scope(c) and not needs.needs_covered_by(c)]
    st.markdown(
        f'<p class="small"><b>이 축의 한계</b>: 사업 {len([c for c in works if in_scope(c)])}건 중 '
        f'<b>{len(um)}건</b>은 원문에 <b>주는 것(수단)이 안 적혀 있어</b> 어떤 수요와도 맞출 수 '
        '없습니다. "덮는 사업이 없다"와 "수단을 못 읽었다"는 다릅니다.</p>',
        unsafe_allow_html=True)


# ═══ 화면 4 — 조치 제안 ═══════════════════════════════════
else:
    st.markdown('<p class="small">판정을 행동으로 옮깁니다. 최종 판단은 담당자가 합니다.</p>',
                unsafe_allow_html=True)
    scoped = [c for c in COV if pick == "전체" or pick in c["industry"]]
    unc = [c for c in scoped if c["verdict"] == "uncovered"]
    thin = [c for c in scoped if c["verdict"] == "covered" and len(c["covers"]) == 1]
    dm = [x for x in findings["dept_mismatch"] if in_scope(by_id[x["pid"]])]
    oh = [f for f in findings["overlaps_harmful"]
          if f.get("same_industry", True) and all(in_scope(by_id[p]) for p in f["items"])]

    st.subheader("먼저 할 것")
    todo = []
    if dm:
        todo.append(("소관 부서를 고치고 협의처를 바꾼다",
                     f"{len(dm)}건의 사업이 공식 예산 원장과 다른 과로 적혀 있습니다. "
                     "공문을 잘못 보내면 회신이 오지 않습니다.", "화면 1"))
    if unc:
        kinds = ", ".join(sorted({c["need"] for c in unc}))
        todo.append((f"「{kinds}」 수요를 덮을 사업을 검토한다",
                     f"{len(unc)}건의 산업 수요에 대응하는 사업이 없습니다. "
                     "먼저 수요조사서가 필요하고, 본예산은 마감됐으니 1차 추경이나 공모가 빠릅니다.",
                     "화면 3"))
    if oh:
        todo.append((f"중복 후보 {len(oh)}건을 부서 협의에 올린다",
                     "받는 사람·주는 것·직무가 모두 같습니다. 확정이 아니라 후보입니다.", "화면 2"))
    if thin:
        todo.append((f"사업 1건에만 의존하는 수요 {len(thin)}건을 표시한다",
                     "그 사업이 멈추면 바로 공백이 됩니다. 예산 심의 때 근거로 씁니다.", "화면 3"))
    if not todo:
        st.success("이 범위에서는 즉시 조치할 항목이 없습니다")
    for i, (t, why, where) in enumerate(todo, 1):
        st.markdown(f'**{i}. {t}**  \n<span class="small">{esc(why)} · 근거는 {where}</span>',
                    unsafe_allow_html=True)

    st.subheader("유도형 산업의 사업 — 수요 대신 무엇으로 정당화할 것인가")
    ind_rows = []
    for c in works:
        if not in_scope(c):
            continue
        ind = industry.industry_of((c.get("name") or "") + str(c.get("summary") or ""))
        if ind and POSTURES.get(ind, {}).get("posture") == industry.INDUCING:
            ind_rows.append((c, ind, industry.inducement_evidence(c, plans)))
    if ind_rows:
        st.markdown('<p class="small">수요 실측치가 없다는 것 자체는 흠이 아닙니다. 대신 아래 셋을 '
                    '답할 수 있어야 "수요도 없는데 왜 하느냐"는 질문을 넘길 수 있습니다.</p>',
                    unsafe_allow_html=True)
        for c, ind, ev in ind_rows[:6]:
            ok = sum(1 for e in ev if e["ok"])
            with st.expander(f"[{ind}] {c['name'][:38]} — 근거 {ok}/3", expanded=(ok == 0)):
                for e in ev:
                    st.markdown(
                        f'<div style="padding:.28rem 0;border-bottom:1px solid var(--rule)">'
                        f'{badge("ok" if e["ok"] else "act", "확보" if e["ok"] else "없음")} '
                        f'<b>{esc(e["test"])}</b> — <span class="small">{esc(e["detail"])}'
                        '</span></div>', unsafe_allow_html=True)
        st.caption("「선점논거」는 어느 원장에도 없습니다. 지어내지 않고 없다고 표시합니다.")
    else:
        st.caption("이 범위에는 유도형 산업 사업이 없습니다")

    st.subheader("이 판정을 그대로 믿으면 안 되는 이유")
    st.markdown(
        '<p class="small">모든 판정은 <b>후보</b>입니다. 확정은 부서 협의로 합니다. '
        '판정에 AI는 관여하지 않습니다 — 원문에서 항목을 뽑는 데만 쓰고, 고르는 일은 규칙이 합니다. '
        '원문에 없는 값은 채우지 않고 <b>비워 둡니다</b>.</p>', unsafe_allow_html=True)
    bad = [c for c in cards if c.get("_name_missing")]
    if bad:
        st.markdown(f'<p class="small">사업명을 읽지 못한 카드 {len(bad)}건이 있습니다 '
                    f'({", ".join(c["policy_id"] for c in bad)}) — 지우지 않고 표시해 뒀습니다.</p>',
                    unsafe_allow_html=True)
