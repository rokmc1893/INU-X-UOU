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
