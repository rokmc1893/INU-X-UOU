"""정책핏 인천 — 4화면 Streamlit 앱 (D-007 · 공무원 UX D-013 · 정책 풀 D-015)."""
import csv
import json
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from engine import detect
from engine.extract import OCCUPATIONS
from engine.store import get_store

st.set_page_config(page_title="정책핏 인천", layout="wide")
load_dotenv()
BASE = Path(__file__).resolve().parent / "data"
ANCHOR = "P001"  # 기준사업: 청년도약기지
TODAY = date(2026, 8, 13)
STAGES = ["교육훈련", "일경험", "구직지원", "매칭", "채용지원", "정착"]

# ── 디자인 토큰: 백서지 + 잉크 네이비 + 인천 항만청색, 판정 신호색 4종 ──
st.markdown("""
<style>
:root{ --ink:#1A2B3C; --paper:#FBFBF9; --harbor:#0E5A8A;
       --gap:#8A8F98; --cut:#C75000; --conflict:#B42318; --parallel:#1E7F4F; }
h1, h2, h3 { color: var(--ink); letter-spacing: -0.01em; }
code, .stg-id { font-family: Consolas, monospace; }
/* 근거등급 칩 */
.chip{ display:inline-block; padding:1px 8px; border-radius:2px; font-size:0.72rem;
       font-weight:600; vertical-align:middle; margin-left:4px; white-space:nowrap;
       border:1px solid transparent; }
.chip.real{ color:var(--harbor); border-color:var(--harbor); background:#0E5A8A0D; }
.chip.verified{ color:var(--parallel); border-color:var(--parallel); background:#1E7F4F0D; }
.chip.virtual{ color:#8a6d00; border-color:#c9a800; background:#fff8dc; }
.chip.press{ color:var(--gap); border-color:var(--gap); background:#8A8F980D; }
.chip.conflict{ color:var(--conflict); border-color:var(--conflict); background:#B423180D; }
.chip.draft{ color:#fff; border-color:var(--cut); background:var(--cut); }
/* 시그니처: 결재란 사슬 */
.chain{ display:flex; align-items:stretch; gap:0; margin:0.6rem 0 1rem 0; }
.stg{ flex:1; border:1.5px solid var(--ink); border-top:5px solid var(--harbor);
      background:#fff; padding:8px 10px; text-align:center; min-width:0; }
.stg.empty{ border-style:dashed; border-top-color:var(--gap); background:transparent; }
.stg.anchor{ border-top-color:var(--cut); }
.stg-name{ font-weight:700; font-size:0.95rem; color:var(--ink); }
.stg-n{ font-size:0.78rem; color:var(--gap); margin-top:2px; }
.lnk{ display:flex; flex-direction:column; justify-content:center; align-items:center;
      width:64px; flex:none; font-size:0.72rem; }
.lnk.cut{ color:var(--cut); }
.lnk.cut .bar{ width:100%; border-top:2px dashed var(--cut); }
.lnk.ok{ color:var(--parallel); }
.lnk.ok .bar{ width:100%; border-top:2px solid var(--parallel); }
.lnk .mark{ margin-top:2px; font-weight:700; }
</style>
""", unsafe_allow_html=True)

# 소관 부서 연락처 — A1 actor registry가 단일 출처 (data/pool/A1_actor_registry.csv)
from engine import refdata
# 2026-08 조직개편으로 원장과 카드의 과 명칭이 다른 경우의 별칭
DEPT_ALIAS = {"AI혁신과": "AI블록체인과"}


def dept_info(dept_text):
    """카드의 owner_dept → (레지스트리 부서명, 정보). 별칭을 먼저 적용한다."""
    if not dept_text:
        return None, None
    for alias, canon in DEPT_ALIAS.items():
        if alias in dept_text:
            return canon, refdata.actors().get(canon)
    return refdata.contact_for(dept_text)


# 판정 → 공무원 다음 행동 번역 (A3 워크플로우 3단계 '유사·중복 검토' 기준)
NEXT_ACTION = {
    "gap": "신규사업 발의 검토 — 수요조사서 확보 후 사업계획서(안) 작성. "
           "2027년 본예산 요구서 마감(6/30)은 지났으므로 1차 추경(2027.1) 또는 공모 대응이 최단 경로.",
    "handoff_break": "두 사업 소관 부서 간 인계 절차 신설 협조공문 발송. "
                     "예산 불요 조치이므로 예산 일정과 무관하게 즉시 착수 가능.",
    "overlap_harmful": "유사·중복 사업 자체 검토서에 통합·조정안 기재, 소관 부서 협의 요청. "
                       "차년도 통폐합 반영: 예산담당관 심사 8~9월.",
    "overlap_intent": "조치 불요 — 검토서에 '의도적 병행' 사유만 기재 (신규 유사사업 발의 방지 근거).",
    "complement": "조치 불요 — 검토서에 '수단이 달라 중복이 아님'을 기재한다. "
                  "A3 3단계 반려사유는 '대상·수단·직무 동일'이므로, 이 기재가 부당 반려를 예방한다.",
}

SCOPES = ["청년일자리 (기본)", "청년일자리 + 바이오"]


@st.cache_resource
def init(scope: str):
    cards = [json.loads(p.read_text(encoding="utf-8"))
             for p in sorted((BASE / "cards").glob("P*.json"))]
    if "바이오" in scope:
        cards += [json.loads(p.read_text(encoding="utf-8"))
                  for p in sorted((BASE / "pool" / "cards").glob("IC-*.json"))]
    demands = []
    dp = BASE / "demand" / "demand_signals.csv"
    if dp.exists():
        with open(dp, encoding="utf-8-sig") as f:
            demands = list(csv.DictReader(f))
    links = refdata.linkages()
    edges = detect.build_edges(cards, demands, links)
    store = get_store()
    store.load(cards, demands)
    store.add_edges(edges)
    findings = detect.run_rules(cards, demands, edges, links)
    return cards, demands, edges, store, findings


st.sidebar.title("정책핏 인천")
scope = st.sidebar.selectbox("분석 범위 — 산업 선택", SCOPES,
                             help="산업을 추가하면 정책 풀에서 관련 정책을 끌어와 함께 진단합니다")
cards, demands, edges, store, findings = init(scope)
by_id = {c["policy_id"]: c for c in cards}

screen = st.sidebar.radio("화면", ["1 검토 개요", "2 정책 연계 지도", "3 유사·중복 검토표", "4 조치 제안서"])
n_real_d = sum(1 for d in demands if d.get("data_type") == "real")
st.sidebar.caption(f"그래프 스토어: **{store.name}**")
st.sidebar.caption(f"정책 {len(cards)}건 · 수요신호 {len(demands)}건 "
                   f"(실신호 {n_real_d}건 · 가상 표본 {len(demands) - n_real_d}건)")
st.sidebar.caption("기준일 2026-08-13 · 모든 판정은 '후보'이며 확정은 부서 협의로")

def _add_card(text: str, prefix: str, label: str):
    """수집·입력 텍스트 → 카드 → 세션 추가. 파이프라인은 배치와 동일하다."""
    from engine.extract import extract_card
    n = len(st.session_state.get("extra_cards", [])) + 1
    card = extract_card(text, f"{prefix}{n:02d}")
    card["origin"] = label
    st.session_state.setdefault("extra_cards", []).append(card)
    return card


with st.sidebar.expander("① 검토할 신규사업(안) 넣기", expanded=True):
    st.caption("A3 3단계 — 발의하려는 사업의 개요를 붙여넣으면 기존 사업과 대조합니다. "
               "신규사업은 공고가 없으므로 URL 대신 이 칸을 씁니다.")
    draft_in = st.text_area(
        "사업기획서(안) 개요",
        height=130,
        placeholder="사업명: 청년 바이오 취업 브릿지\n"
                    "지원대상: 인천 거주 18~39세 미취업 청년\n"
                    "사업내용: 바이오 생산·품질 직무 교육 2개월 + 송도 기업 인턴 3개월\n"
                    "지원규모: 40명")
    if st.button("내 사업으로 대조하기"):
        if not (draft_in or "").strip():
            st.warning("사업 개요를 붙여넣어 주세요.")
        else:
            try:
                head = ("# source_url: (미공고 — 검토 중인 사업안)\n"
                        f"# retrieved_at: {TODAY.isoformat()}\n# data_type: draft\n# ---\n")
                card = _add_card(head + draft_in, "N", "신규사업(안)")
                st.success(f"「{card.get('name') or card['policy_id']}」 대조 시작 — 화면 2·3·4에 반영")
            except Exception as e:
                st.error(f"카드 변환 실패 — 사업명·지원대상·사업내용을 포함해 다시 넣어 주세요. ({type(e).__name__})")

with st.sidebar.expander("② 기존 정책 URL로 가져오기"):
    url_in = st.text_input("정책 안내 페이지 URL", placeholder="https://youth.incheon.go.kr/...")
    if st.button("가져와서 분석에 추가"):
        try:
            from engine.fetch import fetch_policy_text
            card = _add_card(fetch_policy_text(url_in), "U", "URL 수집")
            st.success(f"{card.get('name') or card['policy_id']} 추가됨 — 화면 2·3에 반영")
        except Exception as e:
            st.error(f"가져오기 실패 — 원문 텍스트를 data/policies/raw에 직접 넣어도 됩니다. ({type(e).__name__})")

# URL로 추가된 세션 카드 반영 (파일 저장 없이 세션 한정)
extra = st.session_state.get("extra_cards", [])
if extra:
    cards = cards + extra
    by_id = {c["policy_id"]: c for c in cards}
    links = refdata.linkages()
    edges = detect.build_edges(cards, demands, links)
    findings = detect.run_rules(cards, demands, edges, links)
    # 그래프에도 반영한다 — 카드 구성이 바뀐 경우에만 재적재(매 rerun마다 쓰지 않는다)
    sig = (scope, tuple(c["policy_id"] for c in cards))
    if st.session_state.get("graph_sig") != sig:
        try:
            store.load(cards, demands)
            store.add_edges(edges)
            st.session_state["graph_sig"] = sig
        except Exception as e:
            st.sidebar.warning(f"그래프 재적재 실패 — 판정은 파이썬 규칙으로 계속됩니다. ({type(e).__name__})")
    n_draft = sum(1 for c in extra if c.get("data_type") == "draft")
    label = f"검토 중인 사업안 {n_draft}건" if n_draft else ""
    label += (" · " if label and len(extra) - n_draft else "") + \
             (f"URL 수집 {len(extra) - n_draft}건" if len(extra) - n_draft else "")
    st.sidebar.caption(f"➕ {label} — {store.name}에 적재됨 (세션 한정, 파일 미저장)")


def chip(c) -> str:
    """근거등급 칩. 풀 카드는 evidence_status, 기본 카드는 data_type 기준."""
    if c.get("data_type") == "draft":
        return '<span class="chip draft">검토 중인 사업안</span>'
    ev = c.get("evidence_status")
    if ev == "PRIMARY_VERIFIED":
        return '<span class="chip verified">1차 확인</span>'
    if ev == "SECONDARY_PRESS_ONLY":
        return '<span class="chip press">언론보도 기반</span>'
    if ev == "CONFLICTING_FIGURES":
        return '<span class="chip conflict">수치 충돌</span>'
    if c.get("data_type", "real") == "real":
        return '<span class="chip real">실데이터</span>'
    return '<span class="chip virtual">가상</span>'


def dept_of(pid):
    d = (by_id.get(pid) or {}).get("owner_dept") or "소관 미확인"
    _, info = dept_info(d)
    return f"{d} · ☎ {info['tel']}" if info and info.get("tel") else d


def _is_youth(c):
    t = c.get("target") or {}
    lo, hi = t.get("age_min"), t.get("age_max")
    in_range = lo is not None and hi is not None and lo >= 15 and hi <= 45
    return in_range or "청년" in (c.get("name") or "")


def _is_university_rise(c):
    blob = f"{c.get('name') or ''} {c.get('executor') or ''} {c.get('owner_dept') or ''}"
    return any(k in blob for k in ("대학", "RISE", "학점", "인천대", "인하대", "재능대"))


def a3_reviewers(pids):
    """A3 3단계의 **고정 검토자**를 사업 성격에 따라 반환한다.

    A3 원문: 검토자 = 청년정책담당관(청년사업 시) · 교육협력담당관(대학/RISE 연계 시) · 평가담당관
    소관 부서끼리의 협의와 별개로, 이 검토자들은 사업 성격이 맞으면 반드시 들어간다.
    """
    cs = [by_id[p] for p in pids if p in by_id]
    out = []
    reg = refdata.actors()
    tel = lambda k: (reg.get(k) or {}).get("tel")
    if any(_is_youth(c) for c in cs):
        out.append(("청년정책담당관", tel("청년정책담당관"), "청년사업"))
    if any(_is_university_rise(c) for c in cs):
        out.append(("교육협력담당관", tel("교육협력담당관"), "대학·RISE 연계"))
    out.append(("평가담당관", tel("평가담당관"), "전 사업 공통"))
    return out


def consult_lines(pids):
    """협의 안내 — 소관 부서 + A3 3단계 고정 검토자. 동일 부서면 협조공문이 아니다."""
    raw = [(by_id.get(p) or {}).get("owner_dept") for p in pids]
    owners = {o for o in raw if o}
    out = []
    if any(o is None for o in raw):
        known = ", ".join(sorted(owners)) or "없음"
        out.append(f"소관: 확인된 부서 {known} · **나머지는 소관 미확인** — "
                   "원문에서 주관기관을 추출하지 못했다. 협의 전에 사무분장으로 확인할 것.")
    elif len(owners) == 1:
        out.append(f"소관: {next(iter(owners))} — 두 사업이 같은 부서 소관이므로 "
                   "협조공문이 아니라 부서 내 조정 사안이다.")
    else:
        out.append("소관 협의: " + " ↔ ".join(dept_of(p) for p in pids))
    for name, tel, why in a3_reviewers(pids):
        if any(name in (o or "") for o in owners):
            continue
        out.append(f"A3 3단계 필수 검토자: {name}" + (f" · ☎ {tel}" if tel else "") + f" ({why})")
    return out


def consult_block(pids):
    return "\n\n".join("　" + ln for ln in consult_lines(pids))


def name_of(pid):
    return by_id[pid].get("name") or pid


def chain_html():
    """시그니처: 결재란 사슬 — 인계가 없는 구간은 절단선으로 표시."""
    stage_ids = {s: {c["policy_id"] for c in cards if c.get("stage") == s} for s in STAGES}
    handoff = [(e["src"], e["dst"]) for e in edges if e["type"] == "HANDOFF"]
    parts = []
    for i, s in enumerate(STAGES):
        n = len(stage_ids[s])
        klass = "stg" + (" empty" if n == 0 else "") + (" anchor" if ANCHOR in stage_ids[s] else "")
        parts.append(f'<div class="{klass}"><div class="stg-name">{s}</div>'
                     f'<div class="stg-n">{"정책 없음" if n == 0 else f"{n}건"}</div></div>')
        if i < len(STAGES) - 1:
            nxt = STAGES[i + 1]
            ok = any((a in stage_ids[s] and b in stage_ids[nxt]) or
                     (a in stage_ids[nxt] and b in stage_ids[s]) for a, b in handoff)
            if stage_ids[s] and stage_ids[nxt]:
                cls, mark = ("ok", "인계 있음") if ok else ("cut", "✂ 인계 없음")
            else:
                cls, mark = "cut", "구간 비어 있음"
            parts.append(f'<div class="lnk {cls}"><div class="bar"></div><div class="mark">{mark}</div></div>')
    return '<div class="chain">' + "".join(parts) + "</div>"


def _findings_for(pids):
    """특정 정책들이 걸린 판정만 추린다 (신규사업안 대조용)."""
    out = []
    for f in findings["overlaps_harmful"]:
        if set(f["items"]) & pids:
            out.append(("조정 필요 중복 후보", f["items"], f["reason"]))
    for f in findings["overlaps_intentional"]:
        if set(f["items"]) & pids:
            out.append(("의도적 병행", f["items"], f["reason"]))
    for f in findings.get("complements", []):
        if set(f["items"]) & pids:
            out.append(("보완 관계 · 중복 아님", f["items"], f["reason"]))
    for f in findings["handoff_breaks"]:
        if set(f["items"]) & pids:
            out.append(("인계 공백 후보", f["items"], f["reason"]))
    return out


def draft_report():
    drafts = {c["policy_id"] for c in cards if c.get("data_type") == "draft"}
    lines = ["# 유사·중복 사업 자체 검토서 (초안 — 자동 생성, 담당자 확인 필수)",
             f"작성 기준일: 2026-08-13 · 분석 범위: {scope} · 검토 대상 {len(cards)}건", ""]
    if drafts:
        names = ", ".join(name_of(p) for p in sorted(drafts))
        lines.append(f"## 1. 검토 대상 신규사업(안): {names}")
        lines.append("")
        hits = _findings_for(drafts)
        if hits:
            for kind, items, reason in hits:
                other = " / ".join(name_of(p) for p in items if p not in drafts)
                lines.append(f"- [{kind}] 기존사업 「{other}」 — 사유: {reason}")
                for line in consult_lines(items):
                    lines.append("    - " + line)
        else:
            lines.append("- 규칙상 걸린 기존사업 없음. **단, 이는 '중복 없음'의 증명이 아니라 "
                         "현재 코퍼스 범위에서 후보가 나오지 않았다는 뜻이다.**")
        lines.append("")
        lines.append("### 참고: 분석 범위 전체의 기존사업 간 관계")
        lines.append("")
    for f in findings["overlaps_harmful"]:
        names = " / ".join(name_of(p) for p in f["items"])
        lines.append(f"- [조정 필요 중복 후보] {names} — 사유: {f['reason']} — 조치안: 통합·조정 협의")
        for line in consult_lines(f["items"]):
            lines.append("    - " + line)
    for f in findings["overlaps_intentional"]:
        names = " / ".join(name_of(p) for p in f["items"])
        lines.append(f"- [의도적 병행] {names} — 사유: {f['reason']} — 조치 불요, 사유 기재")
    for f in findings.get("complements", []):
        names = " / ".join(name_of(p) for p in f["items"])
        lines.append(f"- [보완 관계 · 중복 아님] {names} — 사유: {f['reason']}")
    for f in findings["handoff_breaks"]:
        names = " ↔ ".join(name_of(p) for p in f["items"])
        lines.append(f"- [인계 공백 후보] {names} — 조치안: 인계 절차 신설 협의")
        for line in consult_lines(f["items"]):
            lines.append("    - " + line)
    for g in findings["gaps"]:
        lines.append(f"- [지원 공백 후보] 직무 '{g['occupation']}' — {g['reason']} — 조치안: 신규사업 발의 검토")
    lines.append("")
    lines.append("※ 본 문서는 규칙 기반 후보 선별 결과이며, 확정 판정은 부서 협의를 거친다.")
    lines.append("※ 수요신호 일부는 가상 표본 — 공백 판정은 실데이터(고용24 등) 확보 후 재검증 필요.")
    return "\n".join(lines)


if screen.startswith("1"):
    st.title("이 돈은 성과로 이어지고 있는가?")
    st.markdown("**유사·중복 검토를 전화 협의 없이 한 화면에서 — 최종 판단은 담당자가 합니다**")
    st.success("**이 도구가 자동화하는 것** — 신규사업 검토 8단계 중 "
               "**3단계 '타 부서 협의·유사·중복 검토'**(예산 지침 필수 항목)에서 "
               "주무관이 손으로 하던 **기존 사업 대조**. 검토서는 **초안**이며 확정은 부서 협의로 한다.")
    c1, c2, c3, c4, c5 = st.columns(5)
    _gap_occs = sorted({g["occupation"] for g in findings["gaps"]})
    c1.metric("지원 공백 후보", f"{len(_gap_occs)}개 직무",
              help=f"{', '.join(_gap_occs) or '없음'} — 수요신호 {len(findings['gaps'])}건이 "
                   "이 직무를 특정하는 정책 없이 남아 있다. 신규사업 발의 검토 대상.")
    c2.metric("인계 공백 후보", f"{len(findings['handoff_breaks'])}쌍", help="부서 간 협조공문 검토 대상")
    c3.metric("조정 필요 중복 후보", f"{len(findings['overlaps_harmful'])}건",
              help="대상·수단·직무가 같고 상호 인계도 없음 — A3 3단계 반려사유. 검토서 기재 대상")
    c4.metric("의도적 병행", f"{len(findings['overlaps_intentional'])}건",
              help="수단은 같으나 대상이 명시적으로 다름 — 조치 불요, 사유만 기재")
    c5.metric("보완 관계", f"{len(findings.get('complements', []))}건",
              help="같은 단계·대상이나 수단이 다름 — 중복이 아님")
    st.divider()
    st.markdown(f"""
**기준사업: 인천 청년도약기지(취업아카데미)** — 교육훈련 3개월 + 인턴십 3개월, 130명.

질문은 하나다. **교육을 마친 청년이 채용까지 도달하는 사슬이 끊기지 않고 이어지는가?**
정책 {len(cards)}건을 정책 그래프로 적재하고, 규칙이 **공백 · 인계 공백 · 조정 필요 중복 · 의도적 병행 · 보완 관계** 다섯 가지를
후보로 선별한다. 최종 판단은 사람이 한다.
""")
    a = by_id.get(ANCHOR, {})
    st.info(f"[기준사업 원문]({a.get('source_url')}) · 수집 {a.get('retrieved_at')} · "
            f"분석 범위: **{scope}** — 풀에서 산업별 정책을 끌어와 결합 (운영 단계는 6대 산업 전체)")
    st.divider()
    st.subheader("지금 판정하면 언제 반영되나 (2026-08-13 기준)")
    for w in refdata.calendar():
        need = w["inputs"]
        mark = " ✅ 이 도구의 산출물" if "유사중복" in need or "유사·중복" in need else ""
        st.markdown(f"- **{w['type']}** · 착수 {w['start']} · 마감 {w['deadline']}")
        st.caption(f"　필요문서: {need}{mark} · 심사: {w['review']} · 다음 창구: {w['next']} "
                   f"({w['status']})")
    st.caption("출처: 조사자 A의 A2 의사결정 달력 (증거 E021). 연도별 실제 공고일과 대조 필요.")

elif screen.startswith("2"):
    st.title("정책 연계 지도 — 어디서 끊기나")
    st.markdown(chain_html(), unsafe_allow_html=True)
    st.caption("결재란 사슬: 인접 단계 사이에 명시된 인계(HANDOFF)가 있으면 실선, 없으면 절단선(✂). "
               "기준사업이 있는 칸은 주황 상단선.")
    cols = st.columns(len(STAGES))
    for col, stg in zip(cols, STAGES):
        col.markdown(f"**{stg}**")
        for c in cards:
            if c.get("stage") == stg:
                star = "⭐ " if c["policy_id"] == ANCHOR else "· "
                col.markdown(f"{star}[{c.get('name') or c['policy_id']}]({c.get('source_url')}) {chip(c)}",
                             unsafe_allow_html=True)
                dept = (c.get("owner_dept") or "").replace("인천광역시 ", "")
                if dept:
                    col.caption(f"　{dept}")
    unstaged = [c for c in cards if not c.get("stage")]
    if unstaged:
        st.caption("사슬 밖(시설·기업지원·계획 등): " +
                   ", ".join(c.get("name") or c["policy_id"] for c in unstaged))
    st.divider()
    st.subheader("인계 공백 후보 — 구간별 (사업 간 연계 끊김)")
    groups = {}
    for f in findings["handoff_breaks"]:
        groups.setdefault(f["reason"], []).append(f["items"])
    anchor_first = sorted(groups.items(),
                          key=lambda kv: (not any(ANCHOR in pair for pair in kv[1]), kv[0]))
    if not groups:
        st.success("규칙상 인계 공백 후보 없음")
    for reason, pairs in anchor_first:
        with st.expander(f"🔶 {reason} · {len(pairs)}쌍" + (" ⭐" if any(ANCHOR in p for p in pairs) else "")):
            for pair in pairs:
                names = " ↔ ".join(name_of(p) for p in pair)
                st.markdown(f"- {'**' + names + '**' if ANCHOR in pair else names}")
                st.markdown(consult_block(pair))
            st.info(f"→ 다음 행동: {NEXT_ACTION['handoff_break']}")
    st.caption("연락처는 2026-08-13 기준 공개 대표번호이며 발송 전 재확인 필요")
    st.divider()
    if st.button("🔴 라이브: 기준사업 원문 재추출 (gpt-4o)"):
        raw = next((BASE / "policies" / "raw").glob(f"{ANCHOR}_*.txt"))
        try:
            from engine.extract import extract_card
            live = extract_card(raw.read_text(encoding="utf-8"), ANCHOR, model="gpt-4o")
            ts = datetime.now().strftime("%H:%M:%S")
            st.caption(f"호출 시각 {ts} · model=gpt-4o")
            c1, c2 = st.columns(2)
            c1.markdown("**저장 카드 (배치)**")
            c1.json({k: by_id[ANCHOR].get(k) for k in ("stage", "target", "occupation", "missing_fields")})
            c2.markdown("**라이브 재추출**")
            c2.json({k: live.get(k) for k in ("stage", "target", "occupation", "missing_fields")})
        except Exception as e:
            st.error(f"실시간 호출 실패 — 시연은 녹화로 대체합니다. ({type(e).__name__})")

elif screen.startswith("3"):
    st.title("직무별 지원 현황표 (유사·중복 검토표)")
    rows = []
    gap_occs = {g["occupation"]: g["reason"] for g in findings["gaps"]}
    hb_ids = {p for f in findings["handoff_breaks"] for p in f["items"]}
    oh_ids = {p for f in findings["overlaps_harmful"] for p in f["items"]}
    oi_ids = {p for f in findings["overlaps_intentional"] for p in f["items"]}
    for occ in OCCUPATIONS:
        pols = [c for c in cards if occ in (c.get("occupation") or [])]
        marks = []
        if occ in gap_occs:
            marks.append("⬜ 지원 공백")
        if any(c["policy_id"] in hb_ids for c in pols):
            marks.append("🔶 인계 공백")
        if any(c["policy_id"] in oh_ids for c in pols):
            marks.append("🔴 조정 필요 중복")
        if any(c["policy_id"] in oi_ids for c in pols):
            marks.append("🟢 의도적 병행")
        rows.append({"직무": occ, "정책 수": len(pols),
                     "판정(후보)": " · ".join(marks) or "—",
                     "비고": gap_occs.get(occ, ""),
                     "소관 부서": ", ".join(sorted({(c.get("owner_dept") or "?").replace("인천광역시 ", "")
                                                for c in pols})),
                     "정책": ", ".join(c.get("name") or c["policy_id"] for c in pols)})
    st.dataframe(pd.DataFrame(rows), use_container_width=True)
    _real = [d for d in demands if d.get("data_type") == "real"]
    _virt = [d for d in demands if d.get("data_type") != "real"]
    st.caption(f"수요신호 {len(demands)}건 = 조사자 B의 B2 실신호 {len(_real)}건"
               + (f"({', '.join(sorted({d['occupation'] for d in _real}))}, 등급 B~D — "
                  "전국 단위 보고서·사업주체 서술이라 한계 있음)" if _real else "")
               + (f" + 가상 표본 {len(_virt)}건({', '.join(sorted({d['occupation'] for d in _virt}))})"
                  if _virt else "")
               + f" — 공백 판정은 고용24 실데이터 교체 후 확정. 공백 시 → {NEXT_ACTION['gap']}")
    st.caption("광역 컨텍스트: 인천 산업기술인력 부족 1,138명(A급, 시도 단위 — 산업별 분해 불가, B2 D-001)")
    with st.expander("수요신호 상세 — 출처·증거등급·한계"):
        st.dataframe(pd.DataFrame(demands), use_container_width=True)
    if findings["overlaps_harmful"]:
        with st.expander(f"🔴 조정 필요 중복 후보 {len(findings['overlaps_harmful'])}건 — 상세"):
            for f in findings["overlaps_harmful"]:
                st.markdown(f"- {' / '.join(name_of(p) for p in f['items'])} — {f['reason']}")
                st.markdown(consult_block(f['items']))
            st.info(f"→ 다음 행동: {NEXT_ACTION['overlap_harmful']}")
    if findings["overlaps_intentional"]:
        with st.expander(f"🟢 의도적 병행 {len(findings['overlaps_intentional'])}건 — 상세"):
            for f in findings["overlaps_intentional"]:
                st.markdown(f"- {' / '.join(name_of(p) for p in f['items'])} — {f['reason']}")
            st.info(f"→ 다음 행동: {NEXT_ACTION['overlap_intent']}")
    if findings.get("complements"):
        with st.expander(f"🔵 보완 관계 {len(findings['complements'])}건 — 중복이 아님"):
            for f in findings["complements"]:
                st.markdown(f"- {' / '.join(name_of(p) for p in f['items'])} — {f['reason']}")
            st.info(f"→ 다음 행동: {NEXT_ACTION['complement']}")
    with st.expander("[심사위원용] 그래프 질의 원문 (Cypher) — 기술 검증"):
        for qname, q in detect.CYPHER.items():
            st.markdown(f"**{qname}**")
            st.code(q, language="cypher")
        st.caption(
            f"현재 스토어: **{store.name}** · 정책·수요·엣지는 위 그래프에 실제로 적재돼 있다. "
            "위 질의문은 **판정과 동일한 논리를 그래프 질의로 표현한 것**이며, 화면의 판정 수치는 "
            "`detect.run_rules()`의 파이썬 규칙이 계산한다 — 대상 연령·직무 겹침 비교가 앱 계층에 있어 "
            "질의를 그대로 실행하면 행 수가 더 많이 나온다(예: 인계 공백 질의 53행 vs 화면 29쌍).")

elif screen.startswith("4"):
    st.title("조치 제안서 — 최종 판단은 담당자가")
    st.caption(f"분석 범위: **{scope}** — 범위를 바꾸면 판정 후보가 달라집니다 (사이드바)")
    st.markdown("""
| 구분 | 내용 |
|---|---|
| **주조치** | 교육훈련(도약기지)→매칭(대학일자리플러스) 구간의 명시적 인계 절차 신설 |
| **보조조치** | 구직지원 3종(정장·활동비·응시료)의 안내 통합 |
| **새로 필요한 것** | 바이오 생산·품질 직무 연결장치 (청년일자리 범위 기준 공백 후보 — 바이오 풀 결합 시 K-NIBRT 교육과정이 수요를 커버해 공백은 해소되고, 대신 K-NIBRT→매칭·채용 구간의 인계 공백이 드러남) |
| **새로 만들 필요 낮은 것** | 구직지원 신규 사업 — 의도적 병행으로 이미 커버 |
| **추가 검토** | 수요신호 실데이터(고용24) 확보 후 공백 재판정 |
""")
    st.download_button("📄 유사·중복 검토서 초안 다운로드 (.md)", draft_report(),
                       file_name="유사중복_자체검토서_초안_20260813.md")
    st.divider()
    st.subheader("이 판정의 근거 수준 — 추출 정확도 실측")
    rp = BASE / "results.json"
    if rp.exists():
        r = json.loads(rp.read_text(encoding="utf-8"))
        c1, c2, c3, c4 = st.columns(4)
        fmt = lambda v: "—" if v is None else f"{v * 100:.0f}%"
        c1.metric("필드 추출 정확도", fmt(r["field_accuracy"]),
                  help="카드 내용이 원문과 일치하는 비율")
        c2.metric("기권 정확도", fmt(r["abstention_accuracy"]),
                  help="모르는 것을 아는 척하지 않은 비율")
        c3.metric("인용 실재율", fmt(r["span_grounded_rate"]),
                  help="근거 문장이 실제 원문에 존재하는 비율")
        c4.metric("중첩 오판 없음", fmt(r["overlap_correct_rate"]),
                  help="의도적 병행을 중복으로 잘못 지목하지 않은 비율")
        st.caption(f"정답셋 {r['n_cases']}건 (2인 교차판정 확정 전 — 잠정치)")
    else:
        st.warning("results.json 없음 — `python -m engine.evaluate` 실행 필요")
