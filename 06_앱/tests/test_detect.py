from engine.detect import build_edges, run_rules, CYPHER

def card(pid, stage, occ, age=(18, 39), res="인천", emp=None, up=None, down=None, itype="현금지원"):
    return {"policy_id": pid, "name": pid, "stage": stage, "occupation": occ,
            "region": res, "intervention_type": itype,
            "target": {"age_min": age[0], "age_max": age[1],
                       "residency": res, "employment_status": emp},
            "linked_upstream": up or [], "linked_downstream": down or []}

def demand(sid, occ):
    return {"signal_id": sid, "occupation": occ, "geography": "인천",
            "period": "2026", "value": "v", "data_type": "virtual"}

def test_handoff_from_explicit_links():
    cards = [card("P1", "교육훈련", ["바이오생산"], down=["P2"]),
             card("P2", "매칭", ["바이오생산"])]
    edges = build_edges(cards, [])
    assert {"src": "P1", "dst": "P2"} == {k: e[k] for e in edges
                                          if e["type"] == "HANDOFF" for k in ("src", "dst")}

def test_handoff_break_same_target_no_link():
    cards = [card("P1", "교육훈련", ["바이오생산"]),
             card("P2", "매칭", ["바이오생산"])]  # 동일 target·occupation, HANDOFF 없음
    edges = build_edges(cards, [])
    res = run_rules(cards, [], edges)
    assert any(set(f["items"]) == {"P1", "P2"} for f in res["handoff_breaks"])

def test_gap_uncovered_demand():
    cards = [card("P1", "교육훈련", ["SW·AI"])]
    demands = [demand("D1", "바이오품질")]
    edges = build_edges(cards, demands)
    res = run_rules(cards, demands, edges)
    assert res["gaps"][0]["occupation"] == "바이오품질"

def test_covers_edge():
    cards = [card("P1", "교육훈련", ["바이오생산"])]
    demands = [demand("D1", "바이오생산")]
    edges = build_edges(cards, demands)
    assert any(e["type"] == "COVERS" and e["dst"] == "D1"
               and e["props"]["specificity"] == "specific" for e in edges)

def test_generic_cover_is_still_gap():
    cards = [card("P1", "구직지원", ["전직무"])]  # 전직무 일반 지원만 존재
    demands = [demand("D1", "바이오품질")]
    edges = build_edges(cards, demands)
    assert any(e["type"] == "COVERS" and e["props"]["specificity"] == "generic" for e in edges)
    res = run_rules(cards, demands, edges)
    assert res["gaps"] and "일반 지원만" in res["gaps"][0]["reason"]

def test_harmful_overlap_same_everything():
    cards = [card("P1", "구직지원", ["일반사무"]),
             card("P2", "구직지원", ["일반사무"])]  # 같은 stage·occ·target·region, 링크 없음
    edges = build_edges(cards, [])
    res = run_rules(cards, [], edges)
    assert any(set(f["items"]) == {"P1", "P2"} for f in res["overlaps_harmful"])

def test_intentional_overlap_region_differs():
    cards = [card("P1", "구직지원", ["일반사무"], res="인천 중구"),
             card("P2", "구직지원", ["일반사무"], res="인천 연수구")]
    edges = build_edges(cards, [])
    res = run_rules(cards, [], edges)
    assert any(set(f["items"]) == {"P1", "P2"} for f in res["overlaps_intentional"])
    assert not res["overlaps_harmful"]

def test_handoff_break_wildcard_occupation():
    cards = [card("P1", "교육훈련", ["SW·AI"]),
             card("P2", "매칭", ["전직무"])]  # 전직무는 모든 직무와 겹친다
    edges = build_edges(cards, [])
    res = run_rules(cards, [], edges)
    assert any(set(f["items"]) == {"P1", "P2"} for f in res["handoff_breaks"])

def test_means_differ_is_complement_not_overlap():
    """수단이 다르면 중복이 아니라 **보완 관계**로 잡힌다 — 정장 대여 vs 응시료 지원."""
    cards = [card("P1", "구직지원", ["전직무"], itype="현물·물품대여"),
             card("P2", "구직지원", ["전직무"], itype="현금지원")]
    res = run_rules(cards, [], build_edges(cards, []))
    assert not res["overlaps_harmful"] and not res["overlaps_intentional"]
    assert any(set(f["items"]) == {"P1", "P2"} for f in res["complements"])

def test_b3_confirmed_handoff_becomes_edge():
    """조사자 B가 확인한 인계(B3 handoff=YES)는 HANDOFF 엣지가 된다."""
    cards = [card("P1", "교육훈련", ["전직무"]), card("P2", "매칭", ["전직무"])]
    links = [{"a": "P1", "b": "P2", "handoff": "YES", "evidence_id": "L-01"}]
    edges = build_edges(cards, [], links)
    assert any(e["type"] == "HANDOFF" and e["props"]["source"] == "조사 확인(B3)" for e in edges)
    assert not run_rules(cards, [], edges, links)["handoff_breaks"]

def test_b3_not_found_marks_confirmed_absence():
    """B3 handoff=NOT_FOUND는 '조사자가 확인한 부재'로 근거 등급이 올라간다."""
    cards = [card("P1", "교육훈련", ["전직무"]), card("P2", "매칭", ["전직무"])]
    links = [{"a": "P1", "b": "P2", "handoff": "NOT_FOUND", "evidence_id": "L-02"}]
    res = run_rules(cards, [], build_edges(cards, [], links), links)
    assert res["handoff_breaks"][0]["evidence"] == "조사 확인(B3)"

def test_same_means_same_target_is_harmful():
    """수단·대상·직무가 같으면 조정 필요 중복 후보다."""
    cards = [card("P1", "구직지원", ["전직무"], itype="현물·물품대여"),
             card("P2", "구직지원", ["전직무"], itype="현물·물품대여")]
    res = run_rules(cards, [], build_edges(cards, []))
    assert any(set(f["items"]) == {"P1", "P2"} for f in res["overlaps_harmful"])

def test_null_segment_is_not_a_difference():
    """한쪽만 값이 있는 것은 '다름'이 아니라 '미확인' — 중복을 놓치면 안 된다."""
    a = card("P1", "구직지원", ["전직무"], itype="현물·물품대여")
    b = card("P2", "구직지원", ["전직무"], itype="현물·물품대여")
    a["target"]["student_status"] = "재학생 포함"   # b는 키 자체가 없음(=null)
    res = run_rules([a, b], [], build_edges([a, b], []))
    assert any(set(f["items"]) == {"P1", "P2"} for f in res["overlaps_harmful"])

def test_no_openai_import():
    import engine.detect as d, inspect
    src = inspect.getsource(d)
    assert "import openai" not in src and "from openai" not in src

def test_cypher_covers_every_judgment():
    """화면에 노출하는 Cypher가 판정 5종을 빠짐없이 덮는다 — 심사위원이 열어 볼 수 있다."""
    assert set(CYPHER) == {"handoff_breaks", "gaps", "overlaps_harmful",
                           "overlaps_intentional", "complements", "chains", "budget"}


def test_budget_findings_splits_confirmed_and_unverified():
    """예산 원장 대조 — 못 찾은 것은 '예산 없음'이 아니라 '확인 못 함'이다."""
    from engine.detect import budget_findings
    cs = [card("P1", "교육훈련", ["전직무"]), card("P2", "매칭", ["전직무"]),
          card("P3", "구직지원", ["전직무"])]
    table = {"P1": {"status": "EXACT", "dept": "인천", "budget_won": 100},
             "P2": {"status": "NOT_PUBLICLY_VERIFIABLE", "dept": None, "budget_won": None},
             "P3": {"status": "NEEDS_REVIEW", "dept": None, "budget_won": None}}
    r = budget_findings(cs, lambda c: table.get(c["policy_id"]))
    assert [x["pid"] for x in r["budget_confirmed"]] == ["P1"]
    assert [x["pid"] for x in r["budget_unverified"]] == ["P2"]
    assert [x["pid"] for x in r["budget_conflicts"]] == ["P3"]


def test_budget_findings_flags_department_mismatch():
    """카드의 소관과 예산 원장의 소관이 다르면 협의 대상이 달라진다."""
    from engine.detect import budget_findings
    c = card("P1", "교육훈련", ["전직무"])
    c["owner_dept"] = "청년정책담당관"
    r = budget_findings([c], lambda _: {"status": "EXACT", "dept": "반도체바이오과", "budget_won": 1})
    assert r["dept_mismatch"][0]["official"] == "반도체바이오과"


def test_단계가_비면_인계공백으로_보지_않는다():
    """null은 '다른 단계'가 아니라 '단계를 모른다'다.

    실제로 화면에 "교육훈련 다음 None(으)로 넘기는 절차가 없습니다"가 나갔다.
    """
    from engine.detect import run_rules, build_edges
    a = {"policy_id": "A", "stage": "교육훈련", "occupation": ["전직무"], "target": {}}
    b = {"policy_id": "B", "stage": None, "occupation": ["전직무"], "target": {}}
    res = run_rules([a, b], [], build_edges([a, b], [], None))
    assert res["handoff_breaks"] == [], "단계 미상인 사업이 인계 공백으로 잡혔다"


def test_양쪽_단계가_있으면_그대로_잡는다():
    from engine.detect import run_rules, build_edges
    a = {"policy_id": "A", "stage": "교육훈련", "occupation": ["전직무"], "target": {}}
    b = {"policy_id": "B", "stage": "매칭", "occupation": ["전직무"], "target": {}}
    res = run_rules([a, b], [], build_edges([a, b], [], None))
    assert len(res["handoff_breaks"]) == 1
    assert "None" not in res["handoff_breaks"][0]["reason"]
