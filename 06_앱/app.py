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
# ── 디자인: 한국 공문서의 시각 언어 (결재란·괘선·명조 제목) ──
# 산세리프 굵은 제목 + 질문형 헤드라인은 걷어낸다. 공문서는 명사형 제목에 얇은 괘선을 쓴다.
st.markdown("""
<style>
:root{
  --ink:#1A2B3C;      /* 문서 잉크 */
  --paper:#FCFBF8;    /* 백서지 */
  --harbor:#0E5A8A;   /* 인천 항만 청색 — 유일한 강조색, 절제해서 */
  --seal:#B4402E;     /* 관인 주색 — 조치가 필요한 판정에만 */
  --rule:#D6D2C8;     /* 괘선 */
  --muted:#6B7280;
  --serif:Batang,"Nanum Myeongjo","Times New Roman",serif;
}
html,body,[data-testid="stAppViewContainer"]{ background:var(--paper); }
[data-testid="stAppViewContainer"] .main .block-container{ padding-top:1.2rem; max-width:1180px; }

/* 제목 — 공문서 명조. AI 기본값인 굵은 산세리프를 쓰지 않는다 */
h1{ font-family:var(--serif); font-weight:600; font-size:1.85rem; color:var(--ink);
    letter-spacing:-.02em; margin:0 0 .1rem; }
h2{ font-family:var(--serif); font-weight:600; font-size:1.2rem; color:var(--ink);
    border-bottom:1px solid var(--ink); padding-bottom:.25rem; margin:1.8rem 0 .7rem; }
h3{ font-size:1.0rem; font-weight:700; color:var(--ink); margin:1.2rem 0 .4rem; }

/* 문서 머리 — 갑지 상단부 */
.doc-head{ border-top:2.5px solid var(--ink); border-bottom:1px solid var(--rule);
           padding:.55rem 0 .45rem; margin-bottom:1.1rem;
           display:flex; justify-content:space-between; align-items:baseline; gap:1rem; }
.doc-head .t{ font-family:var(--serif); font-size:1.05rem; font-weight:600; color:var(--ink); }
.doc-head .m{ font-size:.76rem; color:var(--muted); font-family:Consolas,monospace; }

/* 진행 — 결재란처럼 칸으로 */
.steps{ display:flex; gap:0; margin:0 0 1.4rem; border:1px solid var(--rule); }
.step{ flex:1; padding:.42rem .5rem; text-align:center; font-size:.8rem; color:var(--muted);
       border-right:1px solid var(--rule); background:#fff; }
.step:last-child{ border-right:0; }
.step .n{ font-family:Consolas,monospace; font-size:.72rem; display:block; opacity:.7; }
.step.on{ background:var(--ink); color:#fff; font-weight:700; }
.step.on .n{ opacity:.85; }
.step.done{ color:var(--ink); }

/* 판정 배지 — 색이 의미를 잃지 않도록 4종만 */
.v{ display:inline-block; padding:.05rem .5rem; font-size:.74rem; font-weight:700;
    border:1px solid; border-radius:1px; white-space:nowrap; }
.v.act{ color:var(--seal); border-color:var(--seal); background:#B4402E0C; }   /* 조치 필요 */
.v.ok{ color:var(--harbor); border-color:var(--harbor); background:#0E5A8A0C; } /* 조치 불요 */
.v.na{ color:var(--muted); border-color:var(--rule); background:#fff; }         /* 근거 부족 */

/* 근거등급 칩 */
.chip{ display:inline-block; padding:0 .42rem; border-radius:1px; font-size:.7rem;
       font-weight:600; vertical-align:middle; margin-left:.28rem; white-space:nowrap;
       border:1px solid; }
.chip.real{ color:var(--harbor); border-color:#9EC3D9; background:#fff; }
.chip.verified{ color:#1E7F4F; border-color:#A9CFBB; background:#fff; }
.chip.virtual{ color:#8a6d00; border-color:#DCC98A; background:#FFFDF3; }
.chip.press{ color:var(--muted); border-color:var(--rule); background:#fff; }
.chip.conflict{ color:var(--seal); border-color:#E0A79B; background:#fff; }
.chip.draft{ color:#fff; border-color:var(--seal); background:var(--seal); }

/* 시그니처: 결재란 사슬 */
.chain{ display:flex; align-items:stretch; margin:.5rem 0 .3rem; }
.stg{ flex:1; border:1px solid var(--ink); border-top:4px solid var(--harbor);
      background:#fff; padding:.55rem .4rem; text-align:center; min-width:0; }
.stg.empty{ border-style:dashed; border-top-color:var(--rule); background:transparent; }
.stg.anchor{ border-top-color:var(--seal); }
.stg-name{ font-family:var(--serif); font-weight:600; font-size:.95rem; color:var(--ink); }
.stg.empty .stg-name{ color:var(--muted); }
.stg-n{ font-size:.72rem; color:var(--muted); margin-top:.15rem; font-family:Consolas,monospace; }
.lnk{ display:flex; flex-direction:column; justify-content:center; align-items:center;
      width:58px; flex:none; font-size:.68rem; }
.lnk.cut{ color:var(--seal); }
.lnk.cut .bar{ width:100%; border-top:1.5px dashed var(--seal); }
.lnk.ok{ color:var(--harbor); }
.lnk.ok .bar{ width:100%; border-top:1.5px solid var(--harbor); }
.lnk .mark{ margin-top:.15rem; font-weight:700; }

/* 지표 — 칸으로, 색은 숫자에만 */
[data-testid="stMetric"]{ background:#fff; border:1px solid var(--rule); padding:.5rem .7rem; }
[data-testid="stMetricValue"]{ font-family:var(--serif); font-size:1.5rem; color:var(--ink); }
[data-testid="stMetricLabel"] p{ font-size:.78rem !important; color:var(--muted); }

/* 안내 박스 — 공문 '붙임' 톤. Streamlit 기본 파스텔을 죽인다 */
[data-testid="stAlert"]{ background:#fff; border:1px solid var(--rule);
                         border-left:3px solid var(--harbor); border-radius:0; }
[data-testid="stAlert"] p{ color:var(--ink); font-size:.86rem; }

/* 표 */
[data-testid="stTable"] table, .stDataFrame{ font-size:.85rem; }
hr{ border-color:var(--rule); }
.small{ font-size:.78rem; color:var(--muted); }
</style>
""", unsafe_allow_html=True)

# 소관 부서 연락처 — A1 actor registry가 단일 출처 (data/pool/A1_actor_registry.csv)
from engine import refdata
from engine import industry
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
    "gap": "이 직무를 위한 사업을 새로 만들지 검토하세요. "
           "먼저 수요조사서가 필요하고, 올해 본예산 신청은 마감됐으니 내년 1차 추경이나 공모가 빠릅니다.",
    "handoff_break": "두 사업 담당 부서에 협조공문을 보내 넘기는 절차를 만드세요. "
                     "돈이 안 드는 조치라 예산 일정과 상관없이 지금 시작할 수 있습니다.",
    "overlap_harmful": "검토서에 '합치거나 조정하겠다'고 쓰고 상대 부서에 협의를 요청하세요. "
                       "통폐합은 예산 심사(8~9월)에 반영됩니다.",
    "overlap_intent": "할 일 없습니다. 검토서에 '일부러 나눠 놓은 것'이라고 이유만 적으세요. "
                      "나중에 비슷한 사업을 또 만들자는 얘기가 나올 때 근거가 됩니다.",
    "complement": "할 일 없습니다. 검토서에 '주는 것이 달라서 중복이 아니다'라고 적으세요. "
                  "중복이라는 이유로 잘못 반려당하는 걸 막아 줍니다.",
}

# 분석 범위 — 값은 풀 카드의 strategic_industry와 대조한다 (None이면 청년일자리만)
SCOPES = {
    "청년일자리 (기본)": None,
    "+ 바이오": ("바이오",),
    "+ 반도체": ("반도체",),
    "+ 로봇": ("로봇",),
    "+ 항공": ("항공",),
    "+ 미래차": ("미래차",),
    "+ 디지털·AI": ("디지털데이터",),
    "+ 6대 전략산업 전체": ("바이오", "반도체", "로봇", "항공",
                       "디지털데이터", "미래차", "공통"),
}

# A2 결정 달력의 두 트랙 = 공무원이 실제로 들어오는 두 경로 (D-025)
PURPOSES = {
    "신규사업 발의": {
        "stage": "다른 부서와 협의하고 비슷한 사업이 있는지 확인하는 단계",
        "track": "다음 연도 본예산 신규사업",
        "input": "사업기획서(안)을 넣고 기존 사업과 대조한다",
        "question": "내가 만들려는 사업이 기존 사업과 중복인가?",
        "doc": "유사·중복 사업 사전 검토",
    },
    "기존사업 개편": {
        "stage": "성과를 평가해서 내년 사업을 고치는 단계",
        "track": "기존사업 개편/확대",
        "input": "개편을 검토할 기존 사업을 고른다",
        "question": "이 사업을 유지할까, 보완할까, 연결할까, 통합할까?",
        "doc": "기존사업 개편 검토",
    },
}


# ── 산업 태세 ── 원칙: 현재 산업은 정책이 맞춰주고, 미래 산업은 정책이 유도한다.
# 태세는 우리가 정하지 않고 조사자 B의 수요신호가 정한다 (engine/industry.py).
_B2 = refdata.b2_rows()
POSTURES = industry.postures(_B2)
_IND_OF = {r["signal_id"]: (r.get("strategic_industry") or "") for r in _B2}


def posture_of_signal(b2_ref):
    """수요신호 하나가 속한 산업의 태세. 복합산업이면 먼저 걸리는 쪽을 쓴다."""
    for part in (_IND_OF.get(b2_ref) or "").split("+"):
        p = POSTURES.get(part.strip())
        if p:
            return p["posture"]
    return None


@st.cache_resource
def init(scope: str):
    cards = [json.loads(p.read_text(encoding="utf-8"))
             for p in sorted((BASE / "cards").glob("P*.json"))]
    inds = SCOPES.get(scope)
    if inds:
        for p in sorted((BASE / "pool" / "cards").glob("IC-*.json")):
            c = json.loads(p.read_text(encoding="utf-8"))
            if any(i in (c.get("strategic_industry") or "") for i in inds):
                cards.append(c)
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
    findings = detect.run_rules(cards, demands, edges, links,
                                posture_of=lambda d: posture_of_signal(d.get("b2_ref")))
    # 조사자 C의 예산 원장 대조 — B가 UNKNOWN이라 한 예산을 C가 확정한 것이 있다
    findings.update(detect.budget_findings(cards, refdata.budget_status_for))
    for c in cards:
        st = refdata.budget_status_for(c)
        if st:
            c["budget_status"] = st["status"]
            if st.get("budget_won") and not c.get("budget"):
                c["budget"] = f"{st['budget_won']:,}원 (공식 원장, C9)"
            if st.get("dept") and not c.get("owner_dept"):
                c["owner_dept"] = st["dept"]
    return cards, demands, edges, store, findings


st.sidebar.title("정책핏 인천")
purpose = st.sidebar.radio(
    "무슨 검토를 하십니까", list(PURPOSES),
    help="인천시 예산 일정에 두 갈래가 따로 있습니다. "
         "실제로는 기존 사업을 고치는 경우가 훨씬 많습니다 — 청년정책 69개 중 85.5%.")
st.sidebar.caption(f"→ {PURPOSES[purpose]['stage']}")
scope = st.sidebar.selectbox("분석 범위 — 산업 선택", list(SCOPES),
                             help="산업을 추가하면 그 산업의 사업들을 함께 불러와 비교합니다")
cards, demands, edges, store, findings = init(scope)
by_id = {c["policy_id"]: c for c in cards}

screen = st.sidebar.radio("화면", ["1 검토 개요", "2 사업 연계 지도", "3 유사·중복 검토표", "4 조치 제안서"])
n_real_d = sum(1 for d in demands if d.get("data_type") == "real")
st.sidebar.caption(f"그래프 스토어: **{store.name}**")
with st.sidebar.expander(f"사업 {len(cards)}건 — 어디서 왔나", expanded=False):
    _raw_n = len(list((BASE / "policies" / "raw").glob("P*.txt")))
    _pool_n = len(cards) - _raw_n
    st.markdown(f"""
**사업 {len(cards)}건**
- 인천청년포털 **원문 직접 수집 {_raw_n}건** — 각 카드에 원문 URL·수집일
{f"- 조사자 B의 사업 원장에서 **{_pool_n}건** — 다수가 언론보도 2차 출처(카드에 등급 표기)" if _pool_n else ""}

**수요신호 {len(demands)}건**
- 조사자 B의 B2 원장 **29건을 읽어** 직무를 특정할 수 있는 **{n_real_d}건만** 신호로 씀
- 나머지 26건은 산업 전체·예산·면적이라 직무에 못 붙임 → 아래 **광역 컨텍스트**로 표시
- 신호가 없는 직무 {len(demands) - n_real_d}종은 **가상 표본**으로 채우고 그렇게 표기함

**부서·달력·연계** — 조사자 A의 A1·A2, 조사자 B의 B3 원장을 그대로 읽는다 (`engine/refdata.py`)
""")
_ctx = refdata.demand_pool()[1]
_ctx_a = [c for c in _ctx if c.get("evidence_grade") == "A" and c.get("value", "").strip()]
if _ctx_a:
    with st.sidebar.expander("광역 컨텍스트 (A급) — 직무에 못 붙인 수치", expanded=False):
        for c in _ctx_a:
            st.markdown(f"- **{c['value']}** · {c['geography']} ({c['b2_ref']})")
        st.caption("시도 단위라 산업·직무별로 분해할 수 없다 — 그래서 판정에 쓰지 않고 배경으로만 둔다.")
st.sidebar.caption("기준일 2026-08-13 · 모든 판정은 '후보'이며 확정은 부서 협의로")

def _add_card(text: str, prefix: str, label: str):
    """수집·입력 텍스트 → 카드 → 세션 추가. 파이프라인은 배치와 동일하다."""
    from engine.extract import extract_card
    n = len(st.session_state.get("extra_cards", [])) + 1
    card = extract_card(text, f"{prefix}{n:02d}")
    card["origin"] = label
    st.session_state.setdefault("extra_cards", []).append(card)
    return card


target_pid = None
if purpose == "기존사업 개편":
    _opts = [c["policy_id"] for c in cards if c.get("name")]
    target_pid = st.sidebar.selectbox(
        "개편을 검토할 사업", _opts, index=_opts.index(ANCHOR) if ANCHOR in _opts else 0,
        format_func=lambda p: (by_id[p].get("name") or p)[:32],
        help="성과를 보고 내년에 고칠지 판단할 사업을 고르세요")

with st.sidebar.expander("① 검토할 신규사업(안) 넣기",
                         expanded=(purpose == "신규사업 발의")):
    st.caption("만들려는 사업의 개요를 붙여넣으면 기존 사업과 비교해 드립니다. "
               "새 사업은 아직 공고가 없으니 주소(URL) 대신 여기에 적으세요.")
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

with st.sidebar.expander("② 기존 사업을 주소로 가져오기"):
    url_in = st.text_input("사업 안내 페이지 주소", placeholder="https://youth.incheon.go.kr/...")
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
    findings = detect.run_rules(cards, demands, edges, links,
                                posture_of=lambda d: posture_of_signal(d.get("b2_ref")))
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
    st.sidebar.caption(f"추가됨: {label} — {store.name}에 적재됨 (세션 한정, 파일 미저장)")


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
        out.append(f"담당 부서: {known} (나머지는 확인 안 됨 — 공고문에 주관기관이 안 적혀 있습니다. "
                   "공문 보내기 전에 사무분장으로 확인하세요)")
    elif len(owners) == 1:
        out.append(f"담당 부서: {next(iter(owners))} — 두 사업이 같은 부서 것이라 "
                   "공문 보낼 필요 없이 부서 안에서 조정하면 됩니다.")
    else:
        out.append("협의할 부서: " + " ↔ ".join(dept_of(p) for p in pids))
    for name, tel, why in a3_reviewers(pids):
        if any(name in (o or "") for o in owners):
            continue
        out.append(f"반드시 함께 검토: {name}" + (f" · ☎ {tel}" if tel else "") + f" — {why}")
    return out


def consult_block(pids):
    return "\n\n".join("　" + ln for ln in consult_lines(pids))


def name_of(pid):
    return by_id[pid].get("name") or pid


PLAN_WORDS = ("기본계획", "종합계획", "발전전략", "5개년", "로드맵", "실행계획", "육성계획")


def is_plan(c):
    """계획·전략 문서인가 — 예산이 붙는 '사업'이 아니라 그 위의 방향 문서다.

    유사·중복 검토의 대상은 사업이지 계획이 아니다. 계획을 사업과 나란히 두고
    '중복'을 따지면 층위가 어긋난다.
    """
    return any(w in (c.get("name") or "") for w in PLAN_WORDS)


def _esc(t):
    return (str(t or "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def chain_svg(focus_pid=None, per_stage=7):
    """정책 간 관계선을 그린다. 노드=정책, 선=인계 / 절취선=인계 공백.

    선을 전부 그리면 실타래가 된다. 그래서 두 가지만 그린다 —
    (1) 확인된 인계(HANDOFF)는 전부, (2) 인계 공백은 **초점 사업에 걸린 것만**.
    나머지 공백은 개수로만 알린다.
    """
    focus = focus_pid or ANCHOR
    # 사슬 밖(시설·R&D·계획)도 열로 그린다 — 조사자 B가 확인한 인계가 이쪽에 몰려 있어서
    # 빼면 '확인된 인계'가 화면에서 사라진다.
    cols = STAGES + ["사슬 밖"]
    staged = {s: [c for c in cards if c.get("stage") == s] for s in STAGES}
    staged["사슬 밖"] = [c for c in cards if not c.get("stage")]
    CW, NW, NH, GAP, TOP = 160, 144, 40, 12, 46
    rows = min(max((len(v) for v in staged.values()), default=0), per_stage)
    H = TOP + rows * (NH + GAP) + 30
    W = CW * len(cols)

    pos, parts, cut_off = {}, [], 0
    for i, s in enumerate(cols):
        x = i * CW + (CW - NW) / 2
        parts.append(f'<text x="{i*CW + CW/2:.0f}" y="24" text-anchor="middle" '
                     f'font-size="13" font-weight="{400 if s == "사슬 밖" else 700}" '
                     f'fill="{"#6B7280" if s == "사슬 밖" else "#1A2B3C"}" '
                     f'font-family="Batang,serif">{s}</text>')
        shown = staged[s][:per_stage]
        if not shown:
            parts.append(f'<rect x="{x:.0f}" y="{TOP}" width="{NW}" height="{NH}" fill="none" '
                         f'stroke="#D6D2C8" stroke-dasharray="4 3"/>'
                         f'<text x="{x + NW/2:.0f}" y="{TOP + NH/2 + 4:.0f}" text-anchor="middle" '
                         f'font-size="11" fill="#6B7280">정책 없음</text>')
        for j, c in enumerate(shown):
            y = TOP + j * (NH + GAP)
            pos[c["policy_id"]] = (x, y)
            is_focus = c["policy_id"] == focus
            nm = (c.get("name") or c["policy_id"])
            label = nm if len(nm) <= 11 else nm[:10] + "…"
            dept = (c.get("owner_dept") or "소관 미확인").replace("인천광역시 ", "")
            parts.append(
                f'<g><title>{_esc(nm)} · {_esc(dept)} · 수단 {_esc(c.get("intervention_type") or "미상")}</title>'
                f'<rect x="{x:.0f}" y="{y}" width="{NW}" height="{NH}" fill="#fff" '
                f'stroke="{"#B4402E" if is_focus else "#1A2B3C"}" '
                f'stroke-width="{2 if is_focus else 1}"/>'
                f'<rect x="{x:.0f}" y="{y}" width="{NW}" height="3" '
                f'fill="{"#B4402E" if is_focus else "#0E5A8A"}"/>'
                f'<text x="{x+8:.0f}" y="{y+18}" font-size="11.5" font-weight="600" '
                f'fill="#1A2B3C">{_esc(label)}</text>'
                f'<text x="{x+8:.0f}" y="{y+32}" font-size="9.5" fill="#6B7280">'
                f'{_esc(dept[:14])}</text></g>')
        if len(staged[s]) > per_stage:
            parts.append(f'<text x="{x:.0f}" y="{TOP + rows*(NH+GAP) + 12:.0f}" font-size="10" '
                         f'fill="#6B7280">외 {len(staged[s]) - per_stage}건</text>')

    def anchor_pts(a, b):
        (x1, y1), (x2, y2) = pos[a], pos[b]
        return (x1 + NW, y1 + NH / 2, x2, y2 + NH / 2) if x1 <= x2 else \
               (x1, y1 + NH / 2, x2 + NW, y2 + NH / 2)

    lines = []
    for e in edges:  # 확인된 인계 — 전부 그린다
        if e["type"] != "HANDOFF" or e["src"] not in pos or e["dst"] not in pos:
            continue
        x1, y1, x2, y2 = anchor_pts(e["src"], e["dst"])
        mx = (x1 + x2) / 2
        confirmed = e.get("props", {}).get("source") == "조사 확인(B3)"
        lines.append(
            f'<path d="M{x1:.0f},{y1:.0f} C{mx:.0f},{y1:.0f} {mx:.0f},{y2:.0f} {x2:.0f},{y2:.0f}" '
            f'fill="none" stroke="#0E5A8A" stroke-width="{2.2 if confirmed else 1.4}" '
            f'marker-end="url(#ar)"><title>인계 있음'
            f'{" (조사 확인 B3)" if confirmed else ""}</title></path>')
    for f in findings["handoff_breaks"]:  # 인계 공백 — 초점 사업 것만
        a, b = f["items"]
        if focus not in (a, b) or a not in pos or b not in pos:
            cut_off += 1
            continue
        x1, y1, x2, y2 = anchor_pts(a, b)
        mx = (x1 + x2) / 2
        lines.append(
            f'<path d="M{x1:.0f},{y1:.0f} C{mx:.0f},{y1:.0f} {mx:.0f},{y2:.0f} {x2:.0f},{y2:.0f}" '
            f'fill="none" stroke="#B4402E" stroke-width="1.3" stroke-dasharray="5 4">'
            f'<title>{_esc(f["reason"])}</title></path>'
            f'<text x="{mx:.0f}" y="{(y1+y2)/2 - 4:.0f}" text-anchor="middle" font-size="11" '
            f'fill="#B4402E" font-weight="700">✂</text>')

    return (f'<svg viewBox="0 0 {W} {H}" width="100%" style="max-width:{W}px;'
            f'background:#fff;border:1px solid #D6D2C8">'
            f'<defs><marker id="ar" markerWidth="7" markerHeight="7" refX="6" refY="3" '
            f'orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#0E5A8A"/></marker></defs>'
            + "".join(lines) + "".join(parts) + "</svg>"), cut_off


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


def renewal_options(pid):
    """A3 8단계의 개편 선택지를 근거와 함께 산출한다.

    결과(result)는 사업 유지·증액/감액·통합·일몰이다. 각 선택지에 **판정 근거가 있는지**를
    같이 돌려주어, 근거 없는 선택지를 고르지 않게 한다.
    """
    c = by_id.get(pid) or {}
    hits = _findings_for({pid})
    kinds = [k for k, _, _ in hits]
    out = []
    has_outcome = bool(c.get("outcome_kpi"))
    has_output = bool(c.get("output_kpi"))

    n_break = sum(1 for k in kinds if "인계" in k)
    if n_break:
        out.append(("연결", f"인계 공백 {n_break}건 — 앞뒤 사업과 이어지는 절차가 문서상 없다",
                    "예산 불요. 협조공문으로 즉시 착수 가능", True))
    n_dup = sum(1 for k in kinds if "중복" in k)
    if n_dup:
        out.append(("통합", f"조정 필요 중복 {n_dup}건 — 대상·수단·직무가 같은 사업이 있다",
                    "A3 3단계 반려사유에 해당. 통폐합은 예산담당관 심사(8~9월)", True))
    n_comp = sum(1 for k in kinds if "보완" in k)
    if n_comp:
        out.append(("유지", f"보완 관계 {n_comp}건 — 겹쳐 보이지만 수단이 달라 중복이 아니다",
                    "검토서에 사유를 기재해 부당한 통폐합을 막는다", True))
    if has_output and not has_outcome:
        out.append(("보완", f"산출 목표는 있으나(`{c.get('output_kpi')}`) **결과 지표가 없다**",
                    "성과평가서 없이는 증액·감액·일몰을 판단할 수 없다", False))
    if not has_output and not has_outcome:
        out.append(("판단 보류", "산출·결과 지표가 모두 원문에 없다",
                    "7단계 성과평가서(비공개)를 확보해야 개편을 논할 수 있다", False))
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


SCREEN_TITLES = ["검토 개요", "사업 연계 지도", "유사·중복 검토표", "조치 제안"]
_idx = int(screen[0]) - 1
st.markdown(
    f'<div class="doc-head"><div class="t">{PURPOSES[purpose]["doc"]}</div>'
    f'<div class="m">정책핏 인천 · {PURPOSES[purpose]["stage"]} · 기준일 2026-08-13</div></div>'
    + '<div class="steps">'
    + "".join(
        f'<div class="step {"on" if i == _idx else ("done" if i < _idx else "")}">'
        f'<span class="n">{i+1}</span>{t}</div>'
        for i, t in enumerate(SCREEN_TITLES))
    + '</div>', unsafe_allow_html=True)

if screen.startswith("1"):
    _p = PURPOSES[purpose]
    st.title("검토 개요")
    st.markdown(f'<p class="small">{_p["question"]} · 예산 트랙 「{_p["track"]}」 · '
                f'이 단계에서 주무관이 손으로 하던 <b>기존 사업 대조</b>를 자동화한다. '
                f'산출물은 <b>검토서 초안</b>이며 확정은 부서 협의로 한다.</p>',
                unsafe_allow_html=True)
    if purpose == "기존사업 개편" and target_pid:
        st.divider()
        _t = by_id[target_pid]
        st.subheader(f"개편 검토 대상: {_t.get('name') or target_pid}")
        st.caption(f"{_t.get('owner_dept') or '소관 미확인'} · "
                   f"수단 {_t.get('intervention_type') or '미상'} · 단계 {_t.get('stage') or '사슬 밖'} · "
                   f"[원문]({_t.get('source_url')})")
        _opts = renewal_options(target_pid)
        if not _opts:
            st.info("다른 사업과의 관계에서는 고칠 이유가 나오지 않았습니다. "
                    "성과평가서를 봐야 판단할 수 있습니다.")
        for name, why, how, grounded in _opts:
            (st.success if grounded else st.warning)(
                f"**{name}** — {why}\n\n　→ {how}"
                + ("" if grounded else "\n\n　⚠ **근거 부족**: 이 선택지는 지금 데이터로 결론 낼 수 없다."))
        st.markdown('<p class="small"><b>돈을 늘릴지 줄일지, 접을지는 여기서 판단할 수 없습니다.</b> '
                    '그러려면 이 사업이 성과를 냈는지 알아야 하는데, 성과평가서는 공개되지 않습니다. '
                    '공개된 자료에 성과지표가 적힌 사업은 넷 중 하나뿐입니다.</p>',
                    unsafe_allow_html=True)
        st.divider()
    c1, c2, c3, c4, c5 = st.columns(5)
    _gap_occs = sorted({g["occupation"] for g in findings["gaps"]})
    c1.metric("지원 공백 후보", f"{len(_gap_occs)}개 직무",
              help=f"{', '.join(_gap_occs) or '없음'} — 수요신호 {len(findings['gaps'])}건이 "
                   "이 직무를 특정하는 정책 없이 남아 있다. 신규사업 발의 검토 대상.")
    c2.metric("인계 공백 후보", f"{len(findings['handoff_breaks'])}쌍", help="앞뒤 사업을 이어 주는 절차가 없는 곳입니다. 협조공문 대상.")
    if len(findings["handoff_breaks"]) > 50:
        st.warning(f"**인계 공백 {len(findings['handoff_breaks'])}쌍은 그대로 검토서에 넣을 수 없다.** "
                   "전수 비교(O(N²))에 '전직무'가 모든 직무와 겹치도록 설계된 결과다. "
                   "실사용에는 우선순위 스코어링과 상위 N건 컷이 필요하며, 아직 구현하지 않았다 — "
                   "지금은 기준사업이 걸린 쌍부터 보이도록 정렬만 해 두었다.")
    c3.metric("조정 필요 중복 후보", f"{len(findings['overlaps_harmful'])}건",
              help="받는 사람·주는 것·직무가 모두 같은 사업 쌍입니다. 검토서에 적어야 합니다.")
    c4.metric("의도적 병행", f"{len(findings['overlaps_intentional'])}건",
              help="주는 것은 같지만 받는 사람이 다릅니다. 할 일은 없고 이유만 적으면 됩니다.")
    c5.metric("보완 관계", f"{len(findings.get('complements', []))}건",
              help="같은 단계지만 주는 것이 달라 중복이 아닙니다.")
    st.divider()
    st.markdown(
        '<table style="width:100%;border-collapse:collapse;font-size:.82rem;margin:.2rem 0 1rem">'
        '<tr style="border-top:1px solid var(--rule);border-bottom:1px solid var(--rule)">'
        '<td style="padding:.4rem .6rem;width:5rem;font-weight:700;color:var(--harbor)">산업</td>'
        '<td style="padding:.4rem .6rem">바이오·반도체·로봇·디지털·미래차·항공 — '
        '<b>사람과 기술이 필요하다고 신호가 나오는 쪽</b></td></tr>'
        '<tr style="border-bottom:1px solid var(--rule)">'
        '<td style="padding:.4rem .6rem;font-weight:700;color:var(--harbor)">정책</td>'
        '<td style="padding:.4rem .6rem">기본계획·종합계획·전략 — <b>방향을 정하는 상위 문서.</b> '
        '예산이 직접 붙지 않아 중복 검토 대상이 아니다</td></tr>'
        '<tr style="border-bottom:1px solid var(--ink)">'
        '<td style="padding:.4rem .6rem;font-weight:700;color:var(--seal)">사업</td>'
        '<td style="padding:.4rem .6rem"><b>예산이 붙는 실행 단위 — 이 도구가 검토하는 대상.</b> '
        '청년도약기지, K-NIBRT 교육과정 같은 것들</td></tr></table>'
        '<p class="small">풀려는 문제는 <b>산업이 필요로 하는 것과 사업이 어긋나는 것</b>입니다. '
        '그래서 둘을 함께 봅니다 — 산업 수요를 덮는 사업이 있는가, 그 사업들이 서로 이어지는가.</p>',
        unsafe_allow_html=True)
    a = by_id.get(ANCHOR, {})
    st.markdown(
        f'<p class="small">기준사업 <b>인천 청년도약기지(취업아카데미)</b> '
        f'교육훈련 3개월 + 인턴십 3개월, 130명 · '
        f'<a href="{a.get("source_url")}">원문</a> · 수집 {a.get("retrieved_at")}<br>'
        f'<b>사업</b> {len(cards)}건을 그래프로 올리고, 규칙이 위 다섯 가지를 <b>후보</b>로 골라냅니다. '
        f'고르는 일에 AI는 관여하지 않습니다.<br>'
        f'검토 단위는 <b>예산이 붙는 사업</b>입니다 — 기본계획·종합계획 같은 상위 문서는 '
        f'중복 검토 대상이 아니라 따로 표시합니다.</p>', unsafe_allow_html=True)
    st.divider()
    st.subheader("예산 반영 시점")
    _my_track = PURPOSES[purpose]["track"]
    for w in refdata.calendar():
        need = w["inputs"]
        mark = "  ← **이 도구의 산출물**" if "유사중복" in need or "유사·중복" in need else ""
        mine = "▸ **검토 중인 트랙** · " if _my_track in w["type"] else ""
        st.markdown(f"- {mine}**{w['type']}** · 착수 {w['start']} · 마감 {w['deadline']}")
        st.caption(f"　필요문서: {need}{mark} · 심사: {w['review']} · 다음 창구: {w['next']} "
                   f"({w['status']})")
    st.caption("출처: 조사자 A의 A2 의사결정 달력 (증거 E021). 연도별 실제 공고일과 대조 필요.")

elif screen.startswith("2"):
    st.title("사업 연계 지도")
    st.markdown('<p class="small">교육훈련부터 정착까지 6단계. 상자 하나가 사업 하나이고, 끊긴 선이 이어지는 절차가 없는 곳입니다.</p>', unsafe_allow_html=True)
    _focus = target_pid or ANCHOR
    _fname = (by_id.get(_focus) or {}).get("name") or _focus
    _svg, _hidden = chain_svg(_focus)
    st.markdown(_svg, unsafe_allow_html=True)
    st.markdown(
        f'<p class="small">'
        f'<span style="color:#0E5A8A">──▶</span> 다음 사업으로 <b>이어짐</b> '
        f'(굵은 선은 조사자가 문서로 확인한 것) &nbsp;·&nbsp; '
        f'<span style="color:#B4402E">┅ ✂</span> 이어지는 절차가 <b>없음</b> &nbsp;·&nbsp; '
        f'<span style="color:#B4402E">▌</span> 지금 보는 사업 <b>{_esc(_fname)}</b><br>'
        f'끊긴 곳을 다 그리면 알아볼 수 없어서 <b>지금 보는 사업의 것만</b> 그렸습니다. '
        f'나머지 {_hidden}쌍은 아래 목록에 있습니다. 상자에 마우스를 올리면 담당 부서가 나옵니다.</p>',
        unsafe_allow_html=True)
    with st.expander("단계별 요약 보기"):
        st.markdown(chain_html(), unsafe_allow_html=True)
        st.markdown('<p class="small">칸 사이에 이어지는 절차가 하나라도 있으면 실선, 없으면 절취선입니다. '
                    '정착 칸이 비어 있으면 취업한 뒤를 돌보는 정책이 없다는 뜻입니다.</p>',
                    unsafe_allow_html=True)
        _plans = [c for c in cards if is_plan(c)]
        _other = [c for c in cards if not c.get("stage") and not is_plan(c)]
        if _plans:
            st.markdown('<p class="small"><b>계획·전략 문서</b> — 사업이 아니라 그 위의 방향 문서입니다. '
                        '예산이 직접 붙지 않아 <b>중복 검토 대상이 아닙니다</b>: '
                        + ", ".join(_esc(c.get("name") or c["policy_id"]) for c in _plans)
                        + '</p>', unsafe_allow_html=True)
        if _other:
            st.markdown('<p class="small"><b>사슬 밖 사업</b> — 시설을 짓거나 기업을 돕는 사업이라 '
                        '사람의 취업 단계에 넣지 않았습니다: '
                        + ", ".join(_esc(c.get("name") or c["policy_id"]) for c in _other)
                        + '</p>', unsafe_allow_html=True)
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
        with st.expander(f"{reason} · {len(pairs)}쌍" + (" ⭐" if any(ANCHOR in p for p in pairs) else "")):
            for pair in pairs:
                names = " ↔ ".join(name_of(p) for p in pair)
                st.markdown(f"- {'**' + names + '**' if ANCHOR in pair else names}")
                st.markdown(consult_block(pair))
            st.info(f"→ 다음 행동: {NEXT_ACTION['handoff_break']}")
    st.caption("연락처는 2026-08-13 기준 공개 대표번호이며 발송 전 재확인 필요")
    st.divider()
    if st.button("기준사업 원문 다시 추출 (gpt-4o 실시간 호출)"):
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
    st.title("유사·중복 검토표")
    st.markdown('<p class="small">먼저 <b>산업이 필요로 하는 것을 사업이 덮고 있는지</b> 보고, '
                '그 다음 <b>사업끼리 겹치는 것이 낭비인지</b>를 가립니다.</p>', unsafe_allow_html=True)

    st.markdown(
        '<div style="border:1px solid var(--ink);padding:.7rem .9rem;margin:.2rem 0 1rem">'
        f'<b>{industry.PRINCIPLE}</b><br>'
        '<span class="small">그래서 산업마다 물어야 할 질문이 다릅니다. '
        '이미 수요가 있는 산업엔 “그 수요를 덮었는가”를, 아직 수요가 없는 산업엔 '
        '“수요를 만들 근거가 있는가”를 묻습니다.</span></div>',
        unsafe_allow_html=True)

    st.subheader("가. 이 산업에 무엇을 물어야 하는가")
    _sel = SCOPES.get(scope) or tuple(industry.INDUSTRIES)
    _prow = ['<table style="width:100%;border-collapse:collapse;font-size:.85rem">'
             '<tr style="border-bottom:1.5px solid var(--ink)">'
             '<th style="text-align:left;padding:.4rem .5rem;width:5.5rem">산업</th>'
             '<th style="text-align:left;padding:.4rem .5rem;width:5rem">태세</th>'
             '<th style="text-align:left;padding:.4rem .5rem">물어야 할 질문</th>'
             '<th style="text-align:left;padding:.4rem .5rem">그렇게 본 이유</th></tr>']
    for _ind in industry.INDUSTRIES:
        if _ind not in _sel:
            continue
        _p = POSTURES[_ind]
        _cls = "ok" if _p["posture"] == industry.RESPONSIVE else "act"
        _prow.append(
            '<tr style="border-bottom:1px solid var(--rule)">'
            f'<td style="padding:.45rem .5rem;font-weight:700">{_esc(_ind)}</td>'
            f'<td style="padding:.45rem .5rem"><span class="v {_cls}">{_p["posture"]}</span></td>'
            f'<td style="padding:.45rem .5rem">{_esc(_p["question"])}</td>'
            f'<td style="padding:.45rem .5rem;font-size:.78rem;color:var(--muted)">'
            f'{_esc(_p["why"])}</td></tr>')
    st.markdown("".join(_prow) + "</table>", unsafe_allow_html=True)
    _resp = [i for i in _sel if POSTURES.get(i, {}).get("posture") == industry.RESPONSIVE]
    st.markdown(
        '<p class="small">태세는 사람이 정한 것이 아니라 <b>수요신호가 정한 것</b>입니다. '
        '여러 시점에서 반복 확인된 공공자료 신호가 있으면 대응형, 단발이거나 언론 서술뿐이면 '
        '유도형입니다. 새 조사 자료가 들어오면 태세도 질문도 저절로 바뀝니다.'
        + (f' 지금 실측 수요가 확인된 산업은 <b>{", ".join(_resp)}</b>뿐입니다.'
           if _resp else ' 지금 실측 수요가 확인된 산업은 없습니다.')
        + '</p>', unsafe_allow_html=True)

    st.subheader("나. 산업 수요를 덮는 사업이 있는가")
    _cov = {}
    for e_ in edges:
        if e_["type"] == "COVERS":
            _cov.setdefault(e_["dst"], []).append((e_["src"], e_["props"].get("specificity")))
    _rows = ['<table style="width:100%;border-collapse:collapse;font-size:.85rem">'
             '<tr style="border-bottom:1.5px solid var(--ink)">'
             '<th style="text-align:left;padding:.4rem .5rem">산업이 필요로 하는 것</th>'
             '<th style="text-align:left;padding:.4rem .5rem;width:6rem">직무</th>'
             '<th style="text-align:left;padding:.4rem .5rem;width:9rem">덮는 사업</th>'
             '<th style="text-align:left;padding:.4rem .5rem">근거</th></tr>']
    for d_ in demands:
        sid = d_["signal_id"]
        spec = [p_ for p_, k in _cov.get(sid, []) if k == "specific"]
        gen = [p_ for p_, k in _cov.get(sid, []) if k == "generic"]
        if spec:
            mark = f'<span class="v ok">{len(spec)}건이 직접 다룸</span>'
        elif gen:
            mark = f'<span class="v act">없음</span><br><span class="small">모든 직무 대상 {len(gen)}건뿐</span>'
        else:
            mark = '<span class="v act">없음</span>'
        real = d_.get("data_type") == "real"
        _rows.append(
            '<tr style="border-bottom:1px solid var(--rule)">'
            f'<td style="padding:.45rem .5rem">{_esc(d_.get("value", "")[:40])}'
            f'{"" if real else chip(d_)}</td>'
            f'<td style="padding:.45rem .5rem;font-weight:700">{_esc(d_["occupation"])}</td>'
            f'<td style="padding:.45rem .5rem">{mark}</td>'
            f'<td style="padding:.45rem .5rem;font-size:.78rem;color:var(--muted)">'
            f'{_esc((d_.get("b2_ref") or "") + " " + (d_.get("evidence_grade") or ""))}'
            f'{" · " + _esc(d_.get("proxy_limit", "")[:38]) if d_.get("proxy_limit") else ""}</td></tr>')
    st.markdown("".join(_rows) + "</table>", unsafe_allow_html=True)
    _uncov = sorted({g["occupation"] for g in findings["gaps"]})
    if _uncov:
        st.markdown(f'<p class="small"><b>{", ".join(_uncov)}</b> — 이 직무를 콕 집어 다루는 사업이 '
                    f'없습니다. {NEXT_ACTION["gap"]}</p>', unsafe_allow_html=True)
    _isig = [s_ for s_ in refdata.industry_signals()
             if any(i in _sel for i in s_["industries"])]
    with st.expander(f"직무는 못 가렸지만 산업은 가려진 신호 {len(_isig)}건 — "
                     "로봇·항공·미래차는 여기 있습니다"):
        st.markdown('<p class="small">위 표는 <b>직무</b>까지 특정된 신호만 씁니다. '
                    '아래는 산업까지만 가려진 신호로, 직무별 대조에는 못 쓰지만 그 산업이 '
                    '어떤 상태인지 말해 줍니다.</p>', unsafe_allow_html=True)
        _ir = ['<table style="width:100%;border-collapse:collapse;font-size:.82rem">'
               '<tr style="border-bottom:1.5px solid var(--ink)">'
               '<th style="text-align:left;padding:.35rem .5rem;width:5rem">산업</th>'
               '<th style="text-align:left;padding:.35rem .5rem">무엇이 확인됐는가</th>'
               '<th style="text-align:left;padding:.35rem .5rem;width:11rem">이 신호의 한계</th></tr>']
        # 근거가 강한 것부터 — 70건을 다 보여주면 A등급 원자료가 언론 서술에 묻힌다
        _isig = sorted(_isig, key=lambda s_: ("ABCD".find(s_["evidence_grade"] or "D"),
                                              s_["trend"] != "SUSTAINED", s_["signal_id"]))
        _shown, _rest = _isig[:24], max(0, len(_isig) - 24)
        for s_ in _shown:
            _ir.append(
                '<tr style="border-bottom:1px solid var(--rule)">'
                f'<td style="padding:.4rem .5rem;font-weight:700">{_esc("/".join(s_["industries"]))}</td>'
                f'<td style="padding:.4rem .5rem">{_esc(s_["problem_type"])}'
                f'<br><span class="small">{_esc(s_["value"][:46])} · {_esc(s_["signal_id"])} '
                f'{_esc(s_["evidence_grade"])}급 {_esc(s_["trend"])}</span></td>'
                f'<td style="padding:.4rem .5rem;font-size:.76rem;color:var(--muted)">'
                f'{_esc(s_["proxy_limit"][:70])}</td></tr>')
        st.markdown("".join(_ir) + "</table>", unsafe_allow_html=True)
        if _rest:
            st.markdown(f'<p class="small">근거가 강한 순으로 24건만 보였습니다. '
                        f'나머지 {_rest}건은 원장 <code>B2_demand_signal.csv</code>에 있습니다 — '
                        '숨긴 것이 아니라 지면 관계로 접었습니다.</p>', unsafe_allow_html=True)

    st.subheader("다. 사업끼리 겹치는 것이 낭비인가")
    gap_occs = {g["occupation"]: g["reason"] for g in findings["gaps"]}
    hb_ids = {p for f in findings["handoff_breaks"] for p in f["items"]}
    oh_ids = {p for f in findings["overlaps_harmful"] for p in f["items"]}
    oi_ids = {p for f in findings["overlaps_intentional"] for p in f["items"]}
    cm_ids = {p for f in findings.get("complements", []) for p in f["items"]}
    badge = lambda cls, txt: f'<span class="v {cls}">{txt}</span>'
    tr = ['<table style="width:100%;border-collapse:collapse;font-size:.86rem">'
          '<tr style="border-bottom:1.5px solid var(--ink)">'
          '<th style="text-align:left;padding:.4rem .5rem">직무</th>'
          '<th style="text-align:right;padding:.4rem .5rem;width:4.5rem">사업</th>'
          '<th style="text-align:left;padding:.4rem .5rem;width:20rem">판정 (후보)</th>'
          '<th style="text-align:left;padding:.4rem .5rem">소관 부서</th></tr>']
    for occ in OCCUPATIONS:
        pols = [c for c in cards if occ in (c.get("occupation") or [])]
        b = []
        if occ in gap_occs:
            b.append(badge("act", "지원 공백"))
        if any(c["policy_id"] in oh_ids for c in pols):
            b.append(badge("act", "조정 필요 중복"))
        if any(c["policy_id"] in hb_ids for c in pols):
            b.append(badge("act", "인계 공백"))
        if any(c["policy_id"] in oi_ids for c in pols):
            b.append(badge("ok", "의도적 병행"))
        if any(c["policy_id"] in cm_ids for c in pols):
            b.append(badge("ok", "보완 관계"))
        depts = sorted({(c.get("owner_dept") or "소관 미확인").replace("인천광역시 ", "") for c in pols})
        tr.append(
            '<tr style="border-bottom:1px solid var(--rule)">'
            f'<td style="padding:.45rem .5rem;font-weight:700">{occ}</td>'
            f'<td style="padding:.45rem .5rem;text-align:right;font-family:Consolas,monospace">{len(pols)}</td>'
            f'<td style="padding:.45rem .5rem">{" ".join(b) or badge("na", "해당 없음")}</td>'
            f'<td style="padding:.45rem .5rem;color:var(--muted);font-size:.8rem">{", ".join(depts) or "—"}</td></tr>')
    st.markdown("".join(tr) + "</table>", unsafe_allow_html=True)
    for occ, why in gap_occs.items():
        st.markdown(f'<p class="small">· <b>{occ}</b> 지원 공백 — {why}</p>', unsafe_allow_html=True)
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
        with st.expander(f"조정 필요 중복 후보 {len(findings['overlaps_harmful'])}건 — 상세"):
            for f in findings["overlaps_harmful"]:
                st.markdown(f"- {' / '.join(name_of(p) for p in f['items'])} — {f['reason']}")
                st.markdown(consult_block(f['items']))
            st.info(f"→ 다음 행동: {NEXT_ACTION['overlap_harmful']}")
    if findings["overlaps_intentional"]:
        with st.expander(f"의도적 병행 {len(findings['overlaps_intentional'])}건 — 상세"):
            for f in findings["overlaps_intentional"]:
                st.markdown(f"- {' / '.join(name_of(p) for p in f['items'])} — {f['reason']}")
            st.info(f"→ 다음 행동: {NEXT_ACTION['overlap_intent']}")
    if findings.get("complements"):
        with st.expander(f"보완 관계 {len(findings['complements'])}건 — 중복이 아님"):
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
    st.title("조치 제안")
    st.markdown(f'<p class="small">판정을 행동으로 옮긴다. 최종 판단은 담당자가 한다. · 분석 범위 {scope}</p>',
                unsafe_allow_html=True)
    # 유도형 산업 사업에는 수요 근거 대신 **다른 근거 3종**을 묻는다.
    # "미래 산업이라 수요가 없다"가 무근거 사업의 면죄부가 되면 안 되기 때문이다 —
    # 실제로 시의회가 양자바이오 사업에 기업 수요 설명을 요구했다(D-110).
    _plans = [c for c in cards if is_plan(c)]
    _induce = []
    for c in cards:
        if is_plan(c):
            continue
        _ind = industry.industry_of((c.get("name") or "") + str(c.get("summary") or ""))
        if _ind and POSTURES.get(_ind, {}).get("posture") == industry.INDUCING:
            _induce.append((c, _ind, industry.inducement_evidence(c, _plans)))
    if _induce:
        st.subheader("수요가 아직 없는 산업의 사업 — 무엇으로 정당화할 것인가")
        st.markdown(
            f'<p class="small">아래 {len(_induce)}건은 <b>유도형 산업</b>의 사업입니다. '
            '수요 실측치가 없다는 것 자체는 흠이 아닙니다. 대신 아래 세 가지를 답할 수 있어야 '
            '“수요도 없는데 왜 하느냐”는 질문을 넘길 수 있습니다.</p>', unsafe_allow_html=True)
        for c, _ind, ev in _induce[:8]:
            _ok = sum(1 for e in ev if e["ok"])
            with st.expander(f"[{_ind}] {c.get('name') or c['policy_id']} — "
                             f"근거 {_ok}/3 확보", expanded=(_ok == 0)):
                for e in ev:
                    _m = "확보" if e["ok"] else "없음"
                    _cl = "ok" if e["ok"] else "act"
                    st.markdown(
                        f'<div style="padding:.3rem 0;border-bottom:1px solid var(--rule)">'
                        f'<span class="v {_cl}">{_m}</span> <b>{e["test"]}</b> — '
                        f'<span class="small">{_esc(e["detail"])}</span></div>',
                        unsafe_allow_html=True)
        st.markdown('<p class="small">“선점논거”는 어느 원장에도 없습니다. 지어내지 않고 '
                    '없다고 표시합니다 — 담당자가 직접 확인할 항목입니다.</p>',
                    unsafe_allow_html=True)
        st.divider()
    if purpose == "기존사업 개편" and target_pid:
        st.subheader(f"「{by_id[target_pid].get('name') or target_pid}」 개편 선택지")
        for name, why, how, grounded in renewal_options(target_pid):
            st.markdown(f"- **{name}** — {why} → {how}"
                        + ("" if grounded else "  ⚠ 근거 부족"))
        st.divider()
    st.markdown("""
| 구분 | 내용 |
|---|---|
| **주조치** | 교육훈련(도약기지)→매칭(대학일자리플러스) 구간의 명시적 인계 절차 신설 |
| **보조조치** | 구직지원 3종(정장·활동비·응시료)의 안내 통합 |
| **새로 필요한 것** | 바이오 생산·품질 직무 연결장치 (청년일자리 범위 기준 공백 후보 — 바이오 풀 결합 시 K-NIBRT 교육과정이 수요를 커버해 공백은 해소되고, 대신 K-NIBRT→매칭·채용 구간의 인계 공백이 드러남) |
| **새로 만들 필요 낮은 것** | 구직지원 신규 사업 — 의도적 병행으로 이미 커버 |
| **추가 검토** | 수요신호 실데이터(고용24) 확보 후 공백 재판정 |
""")
    _bc, _bu = findings.get("budget_confirmed", []), findings.get("budget_unverified", [])
    _bx, _dm = findings.get("budget_conflicts", []), findings.get("dept_mismatch", [])
    if _bc or _bu or _bx or _dm:
        st.subheader("예산 원장 대조")
        st.markdown(
            f'<p class="small">조사자 C가 인천시 공식 예산 원장과 대조한 결과다. '
            f'<b>확인 {len(_bc)}건</b> · 미확인 {len(_bu)}건 · 재검토 {len(_bx)}건 · '
            f'소관 불일치 {len(_dm)}건. '
            f'<b>미확인은 "예산이 없다"가 아니라 "공개 원장에서 찾지 못했다"는 뜻이다.</b></p>',
            unsafe_allow_html=True)
        _won = [b for b in _bc if b.get("budget_won")]
        if _won:
            rows = ['<table style="width:100%;border-collapse:collapse;font-size:.85rem">'
                    '<tr style="border-bottom:1.5px solid var(--ink)">'
                    '<th style="text-align:left;padding:.4rem .5rem">사업</th>'
                    '<th style="text-align:right;padding:.4rem .5rem">공식 예산</th>'
                    '<th style="text-align:left;padding:.4rem .5rem">원장 소관</th>'
                    '<th style="text-align:left;padding:.4rem .5rem">조사자 B가 적은 값</th></tr>']
            for b in sorted(_won, key=lambda x: -x["budget_won"])[:10]:
                rows.append(
                    '<tr style="border-bottom:1px solid var(--rule)">'
                    f'<td style="padding:.4rem .5rem">{_esc(name_of(b["pid"]))}</td>'
                    f'<td style="padding:.4rem .5rem;text-align:right;font-family:Consolas,monospace">'
                    f'{b["budget_won"]:,}</td>'
                    f'<td style="padding:.4rem .5rem;font-size:.8rem">{_esc(b.get("dept") or "—")}</td>'
                    f'<td style="padding:.4rem .5rem;font-size:.8rem;color:var(--muted)">'
                    f'{_esc((b.get("b_said") or "—")[:22])}</td></tr>')
            st.markdown("".join(rows) + "</table>", unsafe_allow_html=True)
            st.markdown('<p class="small">조사자 B의 원장에서 UNKNOWN이던 예산을 C가 공식 원장에서 '
                        '확정했다. 두 조사가 서로를 보완한 결과다.</p>', unsafe_allow_html=True)
        if _dm:
            st.markdown('<p class="small"><b>소관 불일치</b> — 카드의 소관과 예산 원장의 소관이 다르다. '
                        '협의 대상이 달라지므로 확인이 필요하다:<br>'
                        + "<br>".join(f'　{_esc(name_of(m["pid"]))}: 카드 {_esc(m["card"])} '
                                      f'↔ 원장 <b>{_esc(m["official"])}</b>' for m in _dm[:5])
                        + '</p>', unsafe_allow_html=True)
        if _bx:
            st.markdown('<p class="small"><b>재검토 필요</b> — '
                        + ", ".join(_esc(name_of(b["pid"])) for b in _bx)
                        + ' (같은 원장 라인에 두 정책이 잡히는 등 확인이 필요한 건)</p>',
                        unsafe_allow_html=True)
        st.divider()
    st.download_button("유사·중복 검토서 초안 내려받기 (.md)", draft_report(),
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
