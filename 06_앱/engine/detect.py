"""규칙 4종 — 판정에 LLM 불개입. 이 파일에 openai 관련 코드를 넣지 않는다 (스펙 §4)."""
from itertools import combinations

STAGE_ORDER = ["교육훈련", "일경험", "구직지원", "매칭", "채용지원", "정착"]


def _target_overlaps(a, b):
    ta, tb = a.get("target") or {}, b.get("target") or {}
    lo = max(ta.get("age_min") or 0, tb.get("age_min") or 0)
    hi = min(ta.get("age_max") or 200, tb.get("age_max") or 200)
    if lo > hi:
        return False
    ea, eb = ta.get("employment_status"), tb.get("employment_status")
    return ea is None or eb is None or ea == eb


SEGMENT_KEYS = ["residency", "employment_status", "student_status", "income_criteria",
                "age_min", "age_max"]


def _target_differs_explicitly(a, b):
    """대상 세분이 **명시적으로** 다른가.

    한쪽이 null(=원문에 언급 없음)인 것은 '다름'이 아니라 '미확인'이다.
    양쪽에 값이 있고 서로 다를 때만 세분 차이로 인정한다 — 그래야 정보 부족이
    '의도적 병행'으로 둔갑해 진짜 중복을 놓치는 일이 없다.
    """
    ta, tb = a.get("target") or {}, b.get("target") or {}
    for k in SEGMENT_KEYS:
        va, vb = ta.get(k), tb.get(k)
        if va is not None and vb is not None and va != vb:
            return True
    return a.get("region") is not None and b.get("region") is not None \
        and a.get("region") != b.get("region")


def _means_differ(a, b):
    """수단이 명시적으로 다른가 (A3 3단계 반려사유의 '수단' 축)."""
    ia, ib = a.get("intervention_type"), b.get("intervention_type")
    return ia is not None and ib is not None and ia != ib


def _same_industry(a, b):
    """두 사업이 같은 전략산업에 속하는가.

    인계 공백은 O(N²)라 62건에서 273쌍이 나오는데, 그중 210쌍(77%)이 **산업이 서로 다른**
    쌍이었다 — 청년도약기지와 대한항공 MRO 클러스터 사이에 '인계 절차가 없다'고 말하는 것은
    행정적으로 의미가 없다. 지우지는 않고 표시만 해서 화면이 같은 산업 안의 쌍을 먼저 보인다.
    '공통'(전략산업 총괄 계획)과 산업 미상은 어느 쪽과도 짝이 될 수 있다고 본다.
    """
    ia = (a.get("strategic_industry") or "").strip()
    ib = (b.get("strategic_industry") or "").strip()
    if not ia or not ib or "공통" in (ia, ib):
        return True
    # '바이오+디지털데이터'처럼 복합값이 있어 부분 일치로 본다 (B_README: 배타적 분류 아님)
    sa, sb = set(ia.split("+")), set(ib.split("+"))
    return bool(sa & sb)


def _occ_overlap(a, b):
    sa, sb = set(a.get("occupation") or []), set(b.get("occupation") or [])
    if not sa or not sb:
        return False
    if "전직무" in sa or "전직무" in sb:  # 전직무 = 모든 직무와 겹침
        return True
    return bool(sa & sb)


def build_edges(cards, demands, linkages=None):
    """linkages: 조사자 B의 B3 연계근거 (handoff=YES면 확인된 인계, NOT_FOUND면 확인된 부재)."""
    edges = []
    by_name = {}
    for c in cards:
        by_name[c["policy_id"]] = c["policy_id"]
        if c.get("name"):
            by_name[c["name"]] = c["policy_id"]
    ids = {c["policy_id"] for c in cards}
    for lk in linkages or []:  # 조사로 확인된 인계 — LLM 추출보다 근거 등급이 높다
        if lk.get("handoff") == "YES" and lk["a"] in ids and lk["b"] in ids:
            edges.append({"src": lk["a"], "dst": lk["b"], "type": "HANDOFF",
                          "props": {"evidence": lk.get("evidence_id") or "B3",
                                    "source": "조사 확인(B3)"}})
    for c in cards:  # HANDOFF: 원문에 명시된 인계만 (LLM 추출 링크 → 규칙이 엣지화)
        for ref in c.get("linked_downstream") or []:
            if ref in by_name:
                edges.append({"src": c["policy_id"], "dst": by_name[ref],
                              "type": "HANDOFF", "props": {}})
        for ref in c.get("linked_upstream") or []:
            if ref in by_name:
                edges.append({"src": by_name[ref], "dst": c["policy_id"],
                              "type": "HANDOFF", "props": {}})
    for c in cards:  # COVERS — 직무 특정(specific) vs 전직무 일반(generic) 구분
        occs = set(c.get("occupation") or [])
        for d in demands:
            if d["occupation"] in occs:
                edges.append({"src": c["policy_id"], "dst": d["signal_id"],
                              "type": "COVERS", "props": {"specificity": "specific"}})
            elif "전직무" in occs:
                edges.append({"src": c["policy_id"], "dst": d["signal_id"],
                              "type": "COVERS", "props": {"specificity": "generic"}})
    handoff = {(e["src"], e["dst"]) for e in edges if e["type"] == "HANDOFF"}
    for a, b in combinations(cards, 2):  # OVERLAP 2종
        if not (_occ_overlap(a, b) and a.get("stage") == b.get("stage")
                and _target_overlaps(a, b)):
            continue
        pa, pb = a["policy_id"], b["policy_id"]
        if (pa, pb) in handoff or (pb, pa) in handoff:
            continue
        if _means_differ(a, b):
            # 수단이 다르면 중복이 아니라 보완 관계다 (정장 대여 vs 활동비 현금지원)
            edges.append({"src": pa, "dst": pb, "type": "OVERLAP_COMPLEMENTARY",
                          "props": {"reason": f"주는 것이 다릅니다 — "
                                              f"{a.get('intervention_type')} vs {b.get('intervention_type')}"}})
            continue
        if _target_differs_explicitly(a, b):
            edges.append({"src": pa, "dst": pb, "type": "OVERLAP_INTENTIONAL",
                          "props": {"reason": f"주는 것은 같지만({a.get('intervention_type') or '미상'}) "
                                              "받는 사람이나 지역이 다릅니다"}})
        else:
            edges.append({"src": pa, "dst": pb, "type": "OVERLAP_HARMFUL",
                          "props": {"reason": f"받는 사람·주는 것({a.get('intervention_type') or '미상'})·"
                                              "직무가 모두 같습니다"}})
    return edges


def budget_findings(cards, status_of):
    """예산정합성 판정 — 조사자 C의 1순위 모듈.

    status_of(card) → {"status": ..., "budget_won": ..., "dept": ..., ...} 또는 None.
    이름·ID로 예산 원장과 대조한 결과이며, **못 찾은 것은 '예산이 없다'가 아니라 '확인 못 함'**이다.
    """
    confirmed, unverified, conflicts, dept_mismatch = [], [], [], []
    for c in cards:
        st = status_of(c)
        if st is None:
            continue
        s = st.get("status") or ""
        if s in ("EXACT", "RESOLVED", "MATCH_국가직접", "MATCH_부서개편"):
            confirmed.append({"pid": c["policy_id"], **st})
        elif s in ("FUZZY", "PARTIALLY_RESOLVED"):
            confirmed.append({"pid": c["policy_id"], **st, "loose": True})
        elif s.startswith("NOT_PUBLICLY_VERIFIABLE") or s == "CONFIRMED_ABSENT":
            unverified.append({"pid": c["policy_id"], **st})
        elif s == "NEEDS_REVIEW":
            conflicts.append({"pid": c["policy_id"], **st})
        # 소관 부서가 원장과 다르면 협의 대상이 달라진다
        off = (st.get("dept") or "").strip()
        mine = (c.get("owner_dept") or "").strip()
        if off and mine and off not in mine and mine not in off:
            dept_mismatch.append({"pid": c["policy_id"], "card": mine, "official": off})
    return {"budget_confirmed": confirmed, "budget_unverified": unverified,
            "budget_conflicts": conflicts, "dept_mismatch": dept_mismatch}


def run_rules(cards, demands, edges, linkages=None, posture_of=None):
    """posture_of(demand) → '대응형'|'유도형'|'판단보류'|None.

    수요신호가 속한 산업의 태세를 돌려주는 함수. 넘기지 않으면 태세 구분 없이 종전대로
    판정한다(기존 호출부 호환).
    """
    handoff = {(e["src"], e["dst"]) for e in edges if e["type"] == "HANDOFF"}
    # B3에서 '찾아봤는데 인계가 없다'로 확인된 쌍 — 같은 인계 공백이라도 근거 등급이 다르다
    confirmed_absent = {frozenset((lk["a"], lk["b"])) for lk in (linkages or [])
                        if lk.get("handoff") == "NOT_FOUND"}
    res = {"handoff_breaks": [], "gaps": [], "overlaps_harmful": [],
           "overlaps_intentional": [], "complements": []}
    for a, b in combinations(cards, 2):  # 인계 단절: 동일 target·occupation ∧ HANDOFF 없음
        pa, pb = a["policy_id"], b["policy_id"]
        if (_occ_overlap(a, b) and _target_overlaps(a, b)
                and a.get("stage") != b.get("stage")
                and (pa, pb) not in handoff and (pb, pa) not in handoff):
            # 사슬 순서(이른 단계 → 늦은 단계)로 정렬해 표기
            def _idx(c):
                return STAGE_ORDER.index(c.get("stage")) if c.get("stage") in STAGE_ORDER else 99
            first, second = (a, b) if _idx(a) <= _idx(b) else (b, a)
            confirmed = frozenset((pa, pb)) in confirmed_absent
            res["handoff_breaks"].append({
                "items": [first["policy_id"], second["policy_id"]],
                "same_industry": _same_industry(a, b),
                "evidence": "조사 확인(B3)" if confirmed else "원문 미언급",
                "reason": f"{first.get('stage')} 다음 {second.get('stage')}(으)로 넘기는 절차가 문서에 없습니다"
                          + (" (조사자가 직접 찾아봤지만 없었음)" if confirmed else "")})
    covered_specific = {e["dst"] for e in edges if e["type"] == "COVERS"
                        and e["props"].get("specificity") == "specific"}
    covered_generic = {e["dst"] for e in edges if e["type"] == "COVERS"
                       and e["props"].get("specificity") == "generic"}
    for d in demands:  # 공백 후보: 직무를 특정하여 다루는 정책이 없음
        if d["signal_id"] not in covered_specific:
            note = " (모든 직무 대상 일반 지원만 있습니다)" if d["signal_id"] in covered_generic else ""
            # 같은 '공백'이라도 산업 태세에 따라 뜻이 정반대다 (engine/industry.py 참고).
            # 대응형: 이미 있는 수요를 못 덮었다 = 대응 실패. 유도형: 수요 자체가 아직
            # 확인되지 않은 단계 = 공백이 정상일 수 있다. 둘을 같은 말로 쓰면 미래 산업
            # 정책이 전부 '근거 없음'으로 깎인다.
            p = posture_of(d) if posture_of else None
            if p == "유도형":
                meaning = ("아직 수요가 확인되지 않은 산업입니다 — 사업이 없는 것 자체는 "
                           "흠이 아니고, 대신 만들 근거를 물어야 합니다")
            elif p == "대응형":
                meaning = "이미 확인된 수요인데 이 직무를 콕 집어 다루는 사업이 없습니다" + note
            else:
                meaning = "이 직무를 콕 집어 다루는 사업이 없습니다" + note
            res["gaps"].append({"signal_id": d["signal_id"], "occupation": d["occupation"],
                                "posture": p, "reason": meaning})
    by_id = {c["policy_id"]: c for c in cards}
    KEY = {"OVERLAP_HARMFUL": "overlaps_harmful",
           "OVERLAP_INTENTIONAL": "overlaps_intentional",
           "OVERLAP_COMPLEMENTARY": "complements"}
    for e in edges:
        key = KEY.get(e["type"])
        if not key:
            continue
        a, b = by_id.get(e["src"]), by_id.get(e["dst"])
        res[key].append({"items": [e["src"], e["dst"]],
                         "same_industry": _same_industry(a, b) if a and b else True,
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
        "MATCH (d:Demand) WHERE NOT ( (:Policy)-[:COVERS {specificity: 'specific'}]->(d) )\n"
        "RETURN d.signal_id, d.occupation  // 전직무 일반 지원(generic)만으로는 커버로 보지 않음"),
    "overlaps_harmful": (
        "MATCH (a:Policy)-[e:OVERLAP_HARMFUL]->(b:Policy)\n"
        "RETURN a.policy_id, b.policy_id, e.reason"),
    "overlaps_intentional": (
        "MATCH (a:Policy)-[e:OVERLAP_INTENTIONAL]->(b:Policy)\n"
        "RETURN a.policy_id, b.policy_id, e.reason"),
    "chains": (
        "MATCH p=(a:Policy)-[:HANDOFF*2..3]->(b:Policy)\n"
        "WHERE a.policy_id <> b.policy_id\n"
        "RETURN [n IN nodes(p) | n.policy_id] AS 사슬\n"
        "// 쌍 비교로는 나오지 않는 다단계 경로 — 파이썬으로는 순회를 직접 써야 한다"),
    "budget": (
        "MATCH (p:Policy) WHERE p.budget_status IS NOT NULL\n"
        "RETURN p.budget_status AS 상태, count(*) AS 건수, collect(p.name)[0..3] AS 예시\n"
        "// 예산 원장 대조 — 조사자 C의 C0/C9 조인 결과를 노드 속성으로 적재"),
    "complements": (
        "MATCH (a:Policy)-[e:OVERLAP_COMPLEMENTARY]->(b:Policy)\n"
        "RETURN a.policy_id, b.policy_id, e.reason  // 수단이 달라 중복이 아닌 보완 관계"),
}
