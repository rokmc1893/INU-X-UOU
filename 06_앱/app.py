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

# 소관 부서 공개 대표번호 (A1_actor_registry 기준, 2026-08-13 확인)
DEPT_CONTACT = {
    "청년정책담당관": "032-440-2882 (청년일자리팀)",
    "AI블록체인과": "032-440-4342 (AI융합팀)",
    "AI혁신과": "032-440-4342 (AI융합팀)",
    "반도체바이오과": "032-440-4282 (바이오산업팀)",
    "교육협력담당관": "032-440-2142 (RISE추진팀)",
    "예산담당관": "032-440-2252 (예산팀)",
}

# 판정 → 공무원 다음 행동 번역 (A3 워크플로우 3단계 '유사·중복 검토' 기준)
NEXT_ACTION = {
    "gap": "신규사업 발의 검토 — 수요조사서 확보 후 사업계획서(안) 작성. "
           "2027년 본예산 요구서 마감(6/30)은 지났으므로 1차 추경(2027.1) 또는 공모 대응이 최단 경로.",
    "handoff_break": "두 사업 소관 부서 간 인계 절차 신설 협조공문 발송. "
                     "예산 불요 조치이므로 예산 일정과 무관하게 즉시 착수 가능.",
    "overlap_harmful": "유사·중복 사업 자체 검토서에 통합·조정안 기재, 소관 부서 협의 요청. "
                       "차년도 통폐합 반영: 예산담당관 심사 8~9월.",
    "overlap_intent": "조치 불요 — 검토서에 '의도적 병행' 사유만 기재 (신규 유사사업 발의 방지 근거).",
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
    edges = detect.build_edges(cards, demands)
    store = get_store()
    store.load(cards, demands)
    store.add_edges(edges)
    findings = detect.run_rules(cards, demands, edges)
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

with st.sidebar.expander("URL로 정책 가져오기"):
    url_in = st.text_input("정책 안내 페이지 URL", placeholder="https://youth.incheon.go.kr/...")
    if st.button("가져와서 분석에 추가"):
        try:
            from engine.extract import extract_card
            from engine.fetch import fetch_policy_text
            text = fetch_policy_text(url_in)
            pid = f"U{len(st.session_state.get('extra_cards', [])) + 1:02d}"
            card = extract_card(text, pid)
            st.session_state.setdefault("extra_cards", []).append(card)
            st.success(f"{card.get('name') or pid} 추가됨 — 화면 2·3에 반영")
        except Exception as e:
            st.error(f"가져오기 실패 — 원문 텍스트를 data/policies/raw에 직접 넣어도 됩니다. ({type(e).__name__})")

# URL로 추가된 세션 카드 반영 (파일 저장 없이 세션 한정)
extra = st.session_state.get("extra_cards", [])
if extra:
    cards = cards + extra
    by_id = {c["policy_id"]: c for c in cards}
    edges = detect.build_edges(cards, demands)
    findings = detect.run_rules(cards, demands, edges)
    st.sidebar.caption(f"➕ URL로 추가된 정책 {len(extra)}건 (세션 한정)")


def chip(c) -> str:
    """근거등급 칩. 풀 카드는 evidence_status, 기본 카드는 data_type 기준."""
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
    key = next((k for k in DEPT_CONTACT if k in d), None)
    return f"{d} · ☎ {DEPT_CONTACT[key]}" if key else d


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


def draft_report():
    lines = ["# 유사·중복 사업 자체 검토서 (초안 — 자동 생성, 담당자 확인 필수)",
             f"작성 기준일: 2026-08-13 · 분석 범위: {scope} · 검토 대상 {len(cards)}건", ""]
    for f in findings["overlaps_harmful"]:
        names = " / ".join(name_of(p) for p in f["items"])
        lines.append(f"- [조정 필요 중복 후보] {names} — 사유: {f['reason']} — 조치안: 통합·조정 협의 "
                     f"({dept_of(f['items'][0])} ↔ {dept_of(f['items'][1])})")
    for f in findings["overlaps_intentional"]:
        names = " / ".join(name_of(p) for p in f["items"])
        lines.append(f"- [의도적 병행] {names} — 사유: {f['reason']} — 조치 불요, 사유 기재")
    for f in findings["handoff_breaks"]:
        names = " ↔ ".join(name_of(p) for p in f["items"])
        lines.append(f"- [인계 공백 후보] {names} — 조치안: 인계 절차 신설 협조공문 "
                     f"({dept_of(f['items'][0])} ↔ {dept_of(f['items'][1])})")
    for g in findings["gaps"]:
        lines.append(f"- [지원 공백 후보] 직무 '{g['occupation']}' — {g['reason']} — 조치안: 신규사업 발의 검토")
    lines.append("")
    lines.append("※ 본 문서는 규칙 기반 후보 선별 결과이며, 확정 판정은 부서 협의를 거친다.")
    lines.append("※ 수요신호 일부는 가상 표본 — 공백 판정은 실데이터(고용24 등) 확보 후 재검증 필요.")
    return "\n".join(lines)


if screen.startswith("1"):
    st.title("이 돈은 성과로 이어지고 있는가?")
    st.markdown("**유사·중복 검토를 전화 협의 없이 한 화면에서 — 최종 판단은 담당자가 합니다**")
    st.success("**이 도구가 대신하는 업무** — 신규사업 검토 8단계 중 "
               "**3단계 '타 부서 협의·유사·중복 검토'** (예산 지침 필수 항목). "
               "유사·중복 사업 자체 검토서 작성에 필요한 후보를 자동 선별합니다.")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("지원 공백 후보", f"{len(findings['gaps'])}건", help="신규사업 발의 검토 대상")
    c2.metric("인계 공백 후보", f"{len(findings['handoff_breaks'])}쌍", help="부서 간 협조공문 검토 대상")
    c3.metric("조정 필요 중복 후보", f"{len(findings['overlaps_harmful'])}건", help="유사·중복 검토서 기재 대상")
    c4.metric("의도적 병행", f"{len(findings['overlaps_intentional'])}건", help="조치 불요 — 사유만 기재")
    st.divider()
    st.markdown(f"""
**기준사업: 인천 청년도약기지(취업아카데미)** — 교육훈련 3개월 + 인턴십 3개월, 130명.

질문은 하나다. **교육을 마친 청년이 채용까지 도달하는 사슬이 끊기지 않고 이어지는가?**
정책 {len(cards)}건을 정책 그래프로 적재하고, 규칙이 **공백 · 인계 공백 · 조정 필요 중복 · 의도적 병행**을
후보로 선별한다. 최종 판단은 사람이 한다.
""")
    a = by_id.get(ANCHOR, {})
    st.info(f"[기준사업 원문]({a.get('source_url')}) · 수집 {a.get('retrieved_at')} · "
            f"분석 범위: **{scope}** — 풀에서 산업별 정책을 끌어와 결합 (운영 단계는 6대 산업 전체)")
    st.divider()
    st.subheader("지금 판정하면 언제 반영되나 (2026-08-13 기준)")
    WINDOWS = [("RISE 실행계획 수정·연계", date(2026, 11, 30), "9/1 착수 — 교육협력담당관"),
               ("2027년 1차 추경 제출", date(2027, 3, 15), "2027.1.15 착수 — 신규 긴급사업 경로"),
               ("2028년 본예산 신규사업", date(2027, 6, 30), "2027.4 착수 — 정식 신규사업 경로"),
               ("정부 공모 대응", None, "수시 — 공고 후 14~30일, 시비 매칭 확약 필요")]
    for wname, dl, note in WINDOWS:
        dday = f"D-{(dl - TODAY).days}" if dl else "상시"
        st.markdown(f"- **{wname}** · 마감 {dl or '수시'} (**{dday}**) — {note}")
    st.caption("2027년 본예산 요구서(6/30)·하반기 추경(7/31)은 마감 경과 — 차기 창구 기준으로 표시")

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
                st.caption(f"　협의 대상: {dept_of(pair[0])} ↔ {dept_of(pair[1])}")
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
    st.caption("바이오생산 수요는 B2 실신호 기반(B/D급 — 전국 단위 보고서·사업주체 서술이라 한계 있음), "
               "나머지 3건은 가상 표본 — 공백 판정은 고용24 실데이터 교체 후 확정. "
               f"공백 시 → {NEXT_ACTION['gap']}")
    st.caption("광역 컨텍스트: 인천 산업기술인력 부족 1,138명(A급, 시도 단위 — 산업별 분해 불가, B2 D-001)")
    with st.expander("수요신호 상세 — 출처·증거등급·한계"):
        st.dataframe(pd.DataFrame(demands), use_container_width=True)
    if findings["overlaps_harmful"]:
        with st.expander(f"🔴 조정 필요 중복 후보 {len(findings['overlaps_harmful'])}건 — 상세"):
            for f in findings["overlaps_harmful"]:
                st.markdown(f"- {' / '.join(name_of(p) for p in f['items'])} — {f['reason']}")
                st.caption(f"　협의 대상: {dept_of(f['items'][0])} ↔ {dept_of(f['items'][1])}")
            st.info(f"→ 다음 행동: {NEXT_ACTION['overlap_harmful']}")
    if findings["overlaps_intentional"]:
        with st.expander(f"🟢 의도적 병행 {len(findings['overlaps_intentional'])}건 — 상세"):
            for f in findings["overlaps_intentional"]:
                st.markdown(f"- {' / '.join(name_of(p) for p in f['items'])} — {f['reason']}")
            st.info(f"→ 다음 행동: {NEXT_ACTION['overlap_intent']}")
    with st.expander("[심사위원용] 그래프 질의 원문 (Cypher) — 기술 검증"):
        for qname, q in detect.CYPHER.items():
            st.markdown(f"**{qname}**")
            st.code(q, language="cypher")
        st.caption(f"현재 스토어: {store.name}"
                   + ("" if store.name == "Neo4j" else " — Cypher는 Neo4j 가동 시 실행, 지금은 동일 논리 파이썬 규칙"))

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
