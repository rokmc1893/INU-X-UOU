"""규칙 4종 — 판정에 LLM 불개입. 이 파일에 openai 관련 코드를 넣지 않는다 (스펙 §4)."""
from itertools import combinations


def _target_overlaps(a, b):
    ta, tb = a.get("target") or {}, b.get("target") or {}
    lo = max(ta.get("age_min") or 0, tb.get("age_min") or 0)
    hi = min(ta.get("age_max") or 200, tb.get("age_max") or 200)
    if lo > hi:
        return False
    ea, eb = ta.get("employment_status"), tb.get("employment_status")
    return ea is None or eb is None or ea == eb


def _target_equal(a, b):
    return (a.get("target") or {}) == (b.get("target") or {})


def _occ_overlap(a, b):
    return set(a.get("occupation") or []) & set(b.get("occupation") or [])


def build_edges(cards, demands):
    edges = []
    by_name = {}
    for c in cards:
        by_name[c["policy_id"]] = c["policy_id"]
        if c.get("name"):
            by_name[c["name"]] = c["policy_id"]
    for c in cards:  # HANDOFF: 원문에 명시된 인계만 (LLM 추출 링크 → 규칙이 엣지화)
        for ref in c.get("linked_downstream") or []:
            if ref in by_name:
                edges.append({"src": c["policy_id"], "dst": by_name[ref],
                              "type": "HANDOFF", "props": {}})
        for ref in c.get("linked_upstream") or []:
            if ref in by_name:
                edges.append({"src": by_name[ref], "dst": c["policy_id"],
                              "type": "HANDOFF", "props": {}})
    for c in cards:  # COVERS
        occs = set(c.get("occupation") or [])
        for d in demands:
            if d["occupation"] in occs or "전직무" in occs:
                edges.append({"src": c["policy_id"], "dst": d["signal_id"],
                              "type": "COVERS", "props": {}})
    handoff = {(e["src"], e["dst"]) for e in edges if e["type"] == "HANDOFF"}
    for a, b in combinations(cards, 2):  # OVERLAP 2종
        if not (_occ_overlap(a, b) and a.get("stage") == b.get("stage")
                and _target_overlaps(a, b)):
            continue
        pa, pb = a["policy_id"], b["policy_id"]
        if (pa, pb) in handoff or (pb, pa) in handoff:
            continue
        if a.get("region") != b.get("region") or not _target_equal(a, b):
            edges.append({"src": pa, "dst": pb, "type": "OVERLAP_INTENTIONAL",
                          "props": {"reason": "지역 또는 대상 세분이 다름 — 낭비 아님"}})
        else:
            edges.append({"src": pa, "dst": pb, "type": "OVERLAP_HARMFUL",
                          "props": {"reason": "동일 stage·직무·대상·지역, 상호 인계 없음"}})
    return edges


def run_rules(cards, demands, edges):
    handoff = {(e["src"], e["dst"]) for e in edges if e["type"] == "HANDOFF"}
    res = {"handoff_breaks": [], "gaps": [], "overlaps_harmful": [], "overlaps_intentional": []}
    for a, b in combinations(cards, 2):  # 인계 단절: 동일 target·occupation ∧ HANDOFF 없음
        pa, pb = a["policy_id"], b["policy_id"]
        if (_occ_overlap(a, b) and _target_overlaps(a, b)
                and a.get("stage") != b.get("stage")
                and (pa, pb) not in handoff and (pb, pa) not in handoff):
            res["handoff_breaks"].append({
                "items": [pa, pb],
                "reason": f"{a.get('stage')}→{b.get('stage')} 구간에 명시된 인계 없음"})
    covered = {e["dst"] for e in edges if e["type"] == "COVERS"}
    for d in demands:  # 공백 후보
        if d["signal_id"] not in covered:
            res["gaps"].append({"signal_id": d["signal_id"], "occupation": d["occupation"],
                                "reason": "이 수요신호를 커버하는 정책 없음"})
    for e in edges:
        if e["type"] == "OVERLAP_HARMFUL":
            res["overlaps_harmful"].append({"items": [e["src"], e["dst"]],
                                            "reason": e["props"]["reason"]})
        elif e["type"] == "OVERLAP_INTENTIONAL":
            res["overlaps_intentional"].append({"items": [e["src"], e["dst"]],
                                                "reason": e["props"]["reason"]})
    return res


# 동일 논리의 Cypher — Neo4j 가동 시 화면 3 expander에 노출 (스펙 §5.3)
CYPHER = {
    "handoff_breaks": (
        "MATCH (a:Policy), (b:Policy) WHERE a.policy_id < b.policy_id\n"
        "  AND a.stage <> b.stage\n"
        "  AND NOT (a)-[:HANDOFF]-(b)\n"
        "RETURN a.policy_id, b.policy_id  // 동일 대상·직무 겹침은 앱 계층에서 target JSON 비교"),
    "gaps": (
        "MATCH (d:Demand) WHERE NOT ( (:Policy)-[:COVERS]->(d) )\n"
        "RETURN d.signal_id, d.occupation"),
    "overlaps_harmful": (
        "MATCH (a:Policy)-[e:OVERLAP_HARMFUL]->(b:Policy)\n"
        "RETURN a.policy_id, b.policy_id, e.reason"),
    "overlaps_intentional": (
        "MATCH (a:Policy)-[e:OVERLAP_INTENTIONAL]->(b:Policy)\n"
        "RETURN a.policy_id, b.policy_id, e.reason"),
}
