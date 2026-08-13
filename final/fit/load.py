"""데이터 적재 — 06_앱의 검증된 원장을 그대로 읽는다. 복사본을 만들지 않는다."""
import csv
import glob
import json

from . import APP
from engine import detect, refdata, industry

CARDS_GLOB = [str(APP / "data" / "cards" / "P*.json"),
              str(APP / "data" / "pool" / "cards" / "IC-*.json")]

PLAN_WORDS = ("기본계획", "종합계획", "시행계획", "전략", "육성방안", "로드맵", "추진계획")


def is_plan(card):
    """계획·전략 문서인가. 예산이 붙지 않아 중복 검토 대상이 아니다."""
    return any(w in (card.get("name") or "") for w in PLAN_WORDS)


def cards():
    seen = {}
    for pat in CARDS_GLOB:
        for f in sorted(glob.glob(pat)):
            c = json.loads(open(f, encoding="utf-8").read())
            if not c.get("name"):
                # 이름을 못 읽은 카드가 있다(IC-BIO-018). 지우지 않고 표시해 둔다.
                c["name"] = f"(사업명 미확인 · {c['policy_id']})"
                c["_name_missing"] = True
            seen[c["policy_id"]] = c
    return list(seen.values())


def demand_signals():
    p = APP / "data" / "demand" / "demand_signals.csv"
    if not p.exists():
        return []
    with open(p, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def b2():
    return refdata.b2_rows()


def build(cards_list):
    """규칙 판정 일체. 06_앱의 detect를 그대로 쓴다 — 검증된 규칙을 갈라놓지 않는다."""
    ds = demand_signals()
    links = refdata.linkages()
    edges = detect.build_edges(cards_list, ds, links)
    rows = b2()
    postures = industry.postures(rows)
    ind_of = {r["signal_id"]: (r.get("strategic_industry") or "") for r in rows}

    def posture_of(d):
        for part in (ind_of.get(d.get("b2_ref")) or "").split("+"):
            p = postures.get(part.strip())
            if p:
                return p["posture"]
        return None

    findings = detect.run_rules(cards_list, ds, edges, links, posture_of=posture_of)
    findings.update(detect.budget_findings(cards_list, refdata.budget_status_for))
    for c in cards_list:  # 예산 원장에서 확인된 값을 카드에 얹는다
        st = refdata.budget_status_for(c)
        if st:
            c["budget_status"] = st["status"]
            if st.get("budget_won") and not c.get("budget"):
                c["budget"] = f"{st['budget_won']:,}원 (공식 원장, C9)"
            if st.get("dept") and not c.get("owner_dept"):
                c["owner_dept"] = st["dept"]
    return edges, findings, postures
