"""정책핏 인천 — 4화면 Streamlit 앱 (D-007)."""
import csv
import json
from datetime import datetime
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


@st.cache_resource
def init():
    cards = [json.loads(p.read_text(encoding="utf-8"))
             for p in sorted((BASE / "cards").glob("P*.json"))]
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


cards, demands, edges, store, findings = init()
by_id = {c["policy_id"]: c for c in cards}

st.sidebar.title("정책핏 인천")
screen = st.sidebar.radio("화면", ["1 성과 질문", "2 정책사슬 X-ray", "3 커버리지 행렬", "4 판정 카드"])
st.sidebar.caption(f"그래프 스토어: **{store.name}**")
st.sidebar.caption(f"정책 {len(cards)}건 · 수요신호 {len(demands)}건 (수요는 가상 표본)")


def label(card_or_row):
    dt = card_or_row.get("data_type", "real")
    return "🟢 실데이터" if dt == "real" else "🟡 가상데이터"


if screen.startswith("1"):
    st.title("이 돈은 성과로 이어지고 있는가?")
    st.markdown("""
**기준사업: 인천 청년도약기지(취업아카데미)** — 교육훈련 3개월 + 인턴십 3개월, 130명.

질문은 하나다. **교육을 마친 청년이 채용까지 도달하는 사슬이 끊기지 않고 이어지는가?**
이 도구는 인천 청년 일자리 정책 10건을 정책 그래프로 적재하고,
규칙이 **공백 · 인계단절 · 해로운 중첩 · 의도적 중첩**을 판정한다. 최종 판단은 사람이 한다.
""")
    a = by_id.get(ANCHOR, {})
    st.info(f"{label(a)} · [원문]({a.get('source_url')}) · 수집 {a.get('retrieved_at')}")
    st.markdown("분석범위: 인천 청년 일자리·교육훈련 정책 10건 (단일 산업 시연 — 운영 단계는 다산업 확장)")

elif screen.startswith("2"):
    st.title("정책사슬 X-ray")
    stages = ["교육훈련", "일경험", "구직지원", "매칭", "채용지원", "정착"]
    cols = st.columns(len(stages))
    for col, stg in zip(cols, stages):
        col.markdown(f"**{stg}**")
        placed = False
        for c in cards:
            if c.get("stage") == stg:
                col.markdown(f"{'⭐' if c['policy_id'] == ANCHOR else '·'} "
                             f"[{c.get('name') or c['policy_id']}]({c.get('source_url')}) {label(c)}")
                placed = True
        if not placed:
            col.markdown("⬜ *정책 없음*")
    st.divider()
    st.subheader("단절 후보 — 구간별")
    groups = {}
    for f in findings["handoff_breaks"]:
        groups.setdefault(f["reason"], []).append(f["items"])
    anchor_first = sorted(groups.items(),
                          key=lambda kv: (not any(ANCHOR in pair for pair in kv[1]), kv[0]))
    if not groups:
        st.success("규칙상 인계단절 후보 없음")
    for reason, pairs in anchor_first:
        names = ["**" + " ↔ ".join(by_id[p].get("name") or p for p in pair) + "**"
                 if ANCHOR in pair else " ↔ ".join(by_id[p].get("name") or p for p in pair)
                 for pair in pairs]
        with st.expander(f"🔶 {reason} · {len(pairs)}쌍" + (" ⭐" if any(ANCHOR in p for p in pairs) else "")):
            for n in names:
                st.markdown(f"- {n}")
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
    st.title("커버리지 행렬 — 직무 × 판정")
    rows = []
    gap_occs = {g["occupation"]: g["reason"] for g in findings["gaps"]}
    hb_ids = {p for f in findings["handoff_breaks"] for p in f["items"]}
    oh_ids = {p for f in findings["overlaps_harmful"] for p in f["items"]}
    oi_ids = {p for f in findings["overlaps_intentional"] for p in f["items"]}
    for occ in OCCUPATIONS:
        pols = [c for c in cards if occ in (c.get("occupation") or [])]
        marks = []
        if occ in gap_occs:
            marks.append("⬜ 공백")
        if any(c["policy_id"] in hb_ids for c in pols):
            marks.append("🔶 인계단절")
        if any(c["policy_id"] in oh_ids for c in pols):
            marks.append("🔴 해로운 중첩")
        if any(c["policy_id"] in oi_ids for c in pols):
            marks.append("🟢 의도적 중첩")
        rows.append({"직무": occ, "정책 수": len(pols),
                     "판정": " · ".join(marks) or "—",
                     "비고": gap_occs.get(occ, ""),
                     "정책": ", ".join(c.get("name") or c["policy_id"] for c in pols)})
    st.dataframe(pd.DataFrame(rows), use_container_width=True)
    st.caption("수요신호는 가상 표본(🟡)이다 — 공백 판정은 실데이터 교체 후 확정.")
    with st.expander("실행된 규칙 질의 보기 (Cypher)"):
        for name, q in detect.CYPHER.items():
            st.markdown(f"**{name}**")
            st.code(q, language="cypher")
        st.caption(f"현재 스토어: {store.name}"
                   + ("" if store.name == "Neo4j" else " — Cypher는 Neo4j 가동 시 실행, 지금은 동일 논리 파이썬 규칙"))

elif screen.startswith("4"):
    st.title("판정 카드 — 사람이 최종 판단한다")
    st.markdown("""
| 구분 | 내용 |
|---|---|
| **주조치** | 교육훈련(도약기지)→매칭(대학일자리플러스) 구간의 명시적 인계 절차 신설 |
| **보조조치** | 구직지원 3종(정장·활동비·응시료)의 안내 통합 |
| **새로 필요한 것** | 바이오 생산·품질 직무 전용 트랙 (현재 공백 후보 — 전직무 일반 지원만 존재) |
| **새로 만들 필요 낮은 것** | 구직지원 신규 사업 — 의도적 중첩으로 이미 커버 |
| **추가 검토** | 수요신호 실데이터(고용24) 확보 후 공백 재판정 |
""")
    st.divider()
    st.subheader("이 판정의 근거 수준 — 추출 정확도 실측")
    rp = BASE / "results.json"
    if rp.exists():
        r = json.loads(rp.read_text(encoding="utf-8"))
        c1, c2, c3, c4 = st.columns(4)
        fmt = lambda v: "—" if v is None else f"{v * 100:.0f}%"
        c1.metric("필드 추출 정확도", fmt(r["field_accuracy"]))
        c2.metric("기권 정확도", fmt(r["abstention_accuracy"]))
        c3.metric("인용 실재율", fmt(r["span_grounded_rate"]))
        c4.metric("중첩 오판 없음", fmt(r["overlap_correct_rate"]))
        st.caption(f"정답셋 {r['n_cases']}건 (2인 교차판정 확정 전 — 잠정치)")
        if any(c.get("_extraction") == "manual_provisional" for c in cards):
            st.warning("현재 카드는 API 키 확보 전 수동 추출본이다. "
                       "LLM 배치 추출로 교체 후 이 수치를 재측정해야 한다.")
    else:
        st.warning("results.json 없음 — `python -m engine.evaluate` 실행 필요")
