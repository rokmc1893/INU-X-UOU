"""조사자 A·B의 원장을 앱이 읽는 형태로 로드한다.

하드코딩을 없애고 조사 자료를 단일 출처로 삼는다 — 원장이 갱신되면 앱도 따라간다.
출처: 02_조사자료/F4_조사자A(A1·A2), F4_조사자B(B2·B3) → data/pool/ 사본
"""
import csv
from functools import lru_cache
from pathlib import Path

POOL = Path(__file__).resolve().parent.parent / "data" / "pool"

def _map_occupation(row):
    """B2 행 → 우리 직무 통제 어휘. **산업과 직무가 둘 다 특정될 때만** 매핑한다.

    느슨하게 매핑하면 항공 교육생 수가 바이오 수요로 둔갑한다. 직무를 특정할 수 없는
    행은 신호가 아니라 광역 컨텍스트로 분리하는 편이 정직하다.
    """
    ind = row.get("strategic_industry") or ""
    fn = row.get("occupation_or_function") or ""
    if "바이오" in ind:
        if any(k in fn for k in ("QA", "QC", "품질")):
            return "바이오품질"
        if any(k in fn for k in ("공정", "생산", "바이오공정", "GMP")):
            return "바이오생산"
        return None  # 바이오지만 직무 불명 → 컨텍스트
    if ind in ("반도체", "디지털데이터") or "AI" in ind:
        if any(k in fn for k in ("설계", "SW", "소프트웨어", "AI", "인공지능", "데이터")):
            return "SW·AI"
        return None
    return None  # 항공·로봇·미래차는 우리 직무 어휘에 없다 — 매핑하지 않는다


def _rows(name):
    path = POOL / name
    if not path.exists():
        return []
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


@lru_cache(maxsize=1)
def actors():
    """A1 → {부서명: {tel, team, decision_right, source_url}}"""
    out = {}
    for r in _rows("A1_actor_registry.csv"):
        # 카드의 owner_dept는 과·담당관 단위(예: 청년정책담당관)이므로 team을 키로 쓴다.
        key = (r.get("team") or "").strip() or (r.get("department") or "").strip()
        if not key:
            continue
        out[key] = {"tel": (r.get("public_contact") or "").strip(),
                    "bureau": (r.get("department") or "").strip(),
                    "decision_right": (r.get("decision_right") or "").strip(),
                    "document_owned": (r.get("document_owned") or "").strip(),
                    "source_url": (r.get("source_url") or "").strip()}
    return out


def contact_for(dept_text):
    """정책의 owner_dept 문자열에서 A1 레지스트리 항목을 찾는다."""
    if not dept_text:
        return None, None
    for dept, info in actors().items():
        if dept and dept in dept_text:
            return dept, info
    return None, None


@lru_cache(maxsize=1)
def calendar():
    """A2 → 결정 창구 목록. 화면 1의 '언제까지 하면 반영되나'."""
    out = []
    for r in _rows("A2_decision_calendar.csv"):
        out.append({
            "type": (r.get("decision_type") or "").strip(),
            "start": (r.get("practical_start_window") or "").strip(),
            "deadline": (r.get("formal_deadline") or "").strip(),
            "inputs": (r.get("required_input") or "").strip(),
            "review": (r.get("review_body") or "").strip(),
            "next": (r.get("next_available_window") or "").strip(),
            "status": (r.get("confirmed_or_inferred") or "").strip(),
        })
    return out


@lru_cache(maxsize=1)
def demand_pool():
    """B2 29건 → 우리 수요신호 스키마. 직무를 특정할 수 있는 행만 신호로 쓴다.

    직무 매핑이 안 되는 행(산업 일반·예산·면적 등)은 신호가 아니라 **광역 컨텍스트**로 분리한다.
    """
    signals, context = [], []
    for r in _rows("B2_demand_signal.csv"):
        occ = _map_occupation(r)
        row = {
            "signal_id": (r.get("signal_id") or "").replace("-", ""),
            "occupation": occ,
            "geography": (r.get("geography") or "").strip(),
            "period": (r.get("period") or "").strip(),
            "value": f"{r.get('value','')} {r.get('unit','')}".strip(),
            "source_url": (r.get("source_url") or "").strip(),
            "data_type": "real",
            "evidence_grade": (r.get("evidence_grade") or "").strip(),
            "b2_ref": (r.get("signal_id") or "").strip(),
            "proxy_limit": (r.get("proxy_limit") or "").strip(),
            "trend": (r.get("sustained_or_spike") or "").strip(),
        }
        # FORECAST(전망치)는 현재 수요로 쓰지 않는다 — B_README 금지사항
        if occ and row["trend"] != "FORECAST":
            signals.append(row)
        else:
            context.append(row)
    return signals, context


@lru_cache(maxsize=1)
def industry_signals():
    """직무는 특정 못 했지만 **산업은 특정된** 신호.

    직무 통제 어휘가 바이오·SW 5종뿐이라 로봇·항공·미래차 신호가 전부 컨텍스트로 밀려나
    화면에서 사라졌다. 조사자가 조사하지 않은 것이 아니라 **우리 필터가 버린 것**이다.

    직무 단위로는 못 쓰지만 산업 단위로는 쓸 수 있다. 여기서 되살려 산업 태세 판정과
    화면 표시에 쓴다. 직무 신호와 섞지 않도록 별도 목록으로 둔다.
    """
    from .industry import INDUSTRY_KEYWORDS
    out = []
    for r in _rows("B2_demand_signal.csv"):
        if _map_occupation(r):
            continue  # 직무 신호로 이미 잡혔다
        inds = [p.strip() for p in (r.get("strategic_industry") or "").split("+")]
        inds = [i for i in inds if i in INDUSTRY_KEYWORDS]
        if not inds:
            continue  # '공통' 또는 산업 미상 → 광역 컨텍스트로 남긴다
        out.append({
            "signal_id": (r.get("signal_id") or "").strip(),
            "industries": inds,
            "problem_type": (r.get("problem_type") or "").strip(),
            "occupation_raw": (r.get("occupation_or_function") or "").strip(),
            "geography": (r.get("geography") or "").strip(),
            "period": (r.get("period") or "").strip(),
            "value": f"{r.get('value','')} {r.get('unit','')}".strip(),
            "evidence_grade": (r.get("evidence_grade") or "").strip(),
            "proxy_limit": (r.get("proxy_limit") or "").strip(),
            "trend": (r.get("sustained_or_spike") or "").strip(),
            "source_url": (r.get("source_url") or "").strip(),
        })
    return out


@lru_cache(maxsize=1)
def b2_rows():
    """산업 태세 판정용 B2 원본 — industry.posture()에 그대로 넘긴다."""
    return _rows("B2_demand_signal.csv")


def _norm_name(s):
    """정책명 대조용 정규화 — 괄호·공백·중점을 지운다 (C의 '표기 변형 매칭' 문제)."""
    import re
    return re.sub(r"[\s()（）·,\-—]", "", str(s or "")).lower()


@lru_cache(maxsize=1)
def budget_official():
    """C9 → {stable_policy_id: 공식 예산·부서}. 조사자 B가 UNKNOWN이라 한 것을 C가 원장에서 확정했다."""
    out = {}
    for r in _rows("C9_b1_budget_verification.csv"):
        pid = (r.get("stable_policy_id") or "").strip()
        if not pid:
            continue
        won = (r.get("official_budget_won") or "").strip()
        out[pid] = {
            "budget_won": int(won) if won.isdigit() else None,
            "dept": (r.get("official_dept") or "").strip() or None,
            "status": (r.get("verification_status") or "").strip(),
            "b_said": (r.get("B_reported_budget") or "").strip(),
            "source_line": (r.get("official_source_line") or "").strip(),
            "note": (r.get("note") or "").strip(),
        }
    return out


@lru_cache(maxsize=1)
def budget_join():
    """C0 → 정책명 기준 예산 원장 매칭 상태.

    `final_status`가 판정의 근거다 — EXACT/FUZZY는 예산 원장에서 확인된 것,
    NOT_PUBLICLY_VERIFIABLE은 **찾지 못한 것**이지 '예산이 없다'가 아니다.
    """
    out = {}
    for r in _rows("C0_policy_budget_join_final.csv"):
        nm = (r.get("시행계획_과제명") or "").strip()
        if not nm:
            continue
        out[_norm_name(nm)] = {
            "name": nm,
            "budget_item": (r.get("예산_세부사업명") or "").strip() or None,
            "dept": (r.get("담당부서") or "").strip() or None,
            "status": (r.get("final_status") or "").strip(),
        }
    return out


def budget_status_for(card):
    """카드 → 예산 원장 매칭 상태. stable_policy_id(C9) 우선, 없으면 정책명(C0)."""
    pid = card.get("stable_policy_id") or card.get("policy_id")
    off = budget_official().get(pid)
    if off:
        # line = 예산서에 적힌 사업 항목명 / detail = 어떻게 확인했는지 메모.
        # 둘을 한 칸에 합치면 화면에 「어떻게 확인했나」가 항목명 자리에 나온다.
        return {"source": "C9", "status": off["status"], "budget_won": off["budget_won"],
                "dept": off["dept"], "line": off["source_line"],
                "detail": off["note"] or off["source_line"],
                "b_said": off["b_said"]}
    hit = budget_join().get(_norm_name(card.get("name")))
    if hit:
        return {"source": "C0", "status": hit["status"], "budget_won": None,
                "dept": hit["dept"], "line": hit["budget_item"],
                "detail": hit["budget_item"], "b_said": None}
    return None


@lru_cache(maxsize=1)
def linkages():
    """B3 22쌍 → 조사자가 확인한 사업 간 연계.

    handoff 값의 의미가 서로 다르다 — 이 구분이 인계 공백 판정의 근거 등급을 가른다.
      YES       : 인계가 문서로 확인됨 → HANDOFF 엣지를 만든다
      NOT_FOUND : 찾아봤는데 없음 → 인계 공백이 '조사로 확인된' 것이다
      UNKNOWN   : 확인하지 못함 → 공백 여부를 단정할 수 없다
    """
    out = []
    for r in _rows("B3_linkage_evidence.csv"):
        hv = (r.get("handoff") or "UNKNOWN").strip()
        kind = "YES" if hv.startswith("YES") else \
               "NOT_FOUND" if hv.startswith("NOT_FOUND") else "UNKNOWN"
        out.append({"a": (r.get("policy_a") or "").strip(),
                    "b": (r.get("policy_b") or "").strip(),
                    "handoff": kind,
                    "raw": hv,
                    "shared_function": (r.get("shared_function") or "").strip(),
                    "evidence_id": (r.get("evidence_id") or "").strip(),
                    "note": (r.get("note") or "").strip()})
    return out
