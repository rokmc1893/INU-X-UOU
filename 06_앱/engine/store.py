"""GraphStore: Neo4j 주 스토어 + MemoryStore 자동 폴백 (D-010, 스펙 §7)."""
import json
import os


class MemoryStore:
    name = "MemoryStore"

    def __init__(self):
        self._policies, self._demands, self._edges = {}, {}, []

    def load(self, cards, demands):
        self._policies = {c["policy_id"]: c for c in cards}
        self._demands = {d["signal_id"]: d for d in demands}
        self._edges = []

    def add_edges(self, edges):
        self._edges.extend(edges)

    def policies(self):
        return list(self._policies.values())

    def demands(self):
        return list(self._demands.values())

    def edges(self):
        return list(self._edges)


class Neo4jStore:
    name = "Neo4j"

    def __init__(self, uri, user, password):
        from neo4j import GraphDatabase
        self._driver = GraphDatabase.driver(uri, auth=(user, password))
        self._driver.verify_connectivity()

    def load(self, cards, demands):
        with self._driver.session() as s:
            s.run("MATCH (n) DETACH DELETE n")
            for c in cards:
                props = {k: (json.dumps(v, ensure_ascii=False)
                             if isinstance(v, (dict, list)) else v)
                         for k, v in c.items() if not k.startswith("_")}
                s.run("CREATE (:Policy $props)", props=props)
            for d in demands:
                s.run("CREATE (:Demand $props)", props=d)

    def add_edges(self, edges):
        with self._driver.session() as s:
            for e in edges:
                label = "Demand" if e["type"] == "COVERS" else "Policy"
                key = "signal_id" if e["type"] == "COVERS" else "policy_id"
                s.run(
                    f"MATCH (a:Policy {{policy_id: $src}}), (b:{label} {{{key}: $dst}}) "
                    f"CREATE (a)-[:{e['type']} $props]->(b)",
                    src=e["src"], dst=e["dst"], props=e.get("props", {}))

    def _rows(self, query):
        with self._driver.session() as s:
            out = []
            for r in s.run(query):
                d = dict(r["n"])
                for k in ("target", "occupation", "source_span", "missing_fields",
                          "linked_upstream", "linked_downstream"):
                    if isinstance(d.get(k), str):
                        try:
                            d[k] = json.loads(d[k])
                        except (json.JSONDecodeError, TypeError):
                            pass
                out.append(d)
            return out

    def policies(self):
        return self._rows("MATCH (n:Policy) RETURN n")

    def demands(self):
        return self._rows("MATCH (n:Demand) RETURN n")

    def edges(self):
        with self._driver.session() as s:
            return [{"src": r["src"], "dst": r["dst"], "type": r["type"],
                     "props": dict(r["props"])}
                    for r in s.run(
                        "MATCH (a)-[e]->(b) RETURN coalesce(a.policy_id,a.signal_id) AS src, "
                        "coalesce(b.policy_id,b.signal_id) AS dst, type(e) AS type, properties(e) AS props")]


def get_store():
    """Neo4j 연결 시도 → 실패하면 MemoryStore (앱 시작 시 화면에 store.name 표시)."""
    try:
        return Neo4jStore(
            os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
            os.environ.get("NEO4J_USER", "neo4j"),
            os.environ.get("NEO4J_PASSWORD", ""))
    except Exception:
        return MemoryStore()
