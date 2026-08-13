"""cards → Neo4j 적재 스크립트(.cypher). 질의응답용 산출물 (D-010)."""
import json
from pathlib import Path


def _props(d, skip_private=True):
    parts = []
    for k, v in d.items():
        if skip_private and k.startswith("_"):
            continue
        if isinstance(v, (dict, list)):
            v = json.dumps(v, ensure_ascii=False)
        parts.append(f"{k}: {json.dumps(v, ensure_ascii=False)}")
    return "{" + ", ".join(parts) + "}"


def export_cypher(cards, demands, edges) -> str:
    lines = ["// 정책핏 인천 — Neo4j 적재 스크립트 (자동 생성)", "MATCH (n) DETACH DELETE n;"]
    for c in cards:
        lines.append(f"CREATE (:Policy {_props(c)});")
    for d in demands:
        lines.append(f"CREATE (:Demand {_props(d)});")
    for e in edges:
        label = "Demand" if e["type"] == "COVERS" else "Policy"
        key = "signal_id" if e["type"] == "COVERS" else "policy_id"
        lines.append(
            f"MATCH (a:Policy {{policy_id: {json.dumps(e['src'])}}}), "
            f"(b:{label} {{{key}: {json.dumps(e['dst'])}}}) "
            f"CREATE (a)-[:{e['type']} {_props(e.get('props', {}))}]->(b);")
    return "\n".join(lines)


if __name__ == "__main__":
    base = Path(__file__).resolve().parent.parent / "data"
    cards = [json.loads(p.read_text(encoding="utf-8"))
             for p in sorted((base / "cards").glob("P*.json"))]
    import csv
    demands = []
    dpath = base / "demand" / "demand_signals.csv"
    if dpath.exists():
        with open(dpath, encoding="utf-8-sig") as f:
            demands = list(csv.DictReader(f))
    from engine.detect import build_edges
    text = export_cypher(cards, demands, build_edges(cards, demands))
    (base / "graph_load.cypher").write_text(text, encoding="utf-8")
    print(f"data/graph_load.cypher 생성 — {len(cards)} 정책, {len(demands)} 수요")
