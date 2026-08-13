from engine.detect import build_edges, run_rules, CYPHER

def card(pid, stage, occ, age=(18, 39), res="인천", emp=None, up=None, down=None):
    return {"policy_id": pid, "name": pid, "stage": stage, "occupation": occ,
            "region": res,
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

def test_no_openai_import():
    import engine.detect as d, inspect
    src = inspect.getsource(d)
    assert "import openai" not in src and "from openai" not in src

def test_cypher_has_all_rules():
    assert set(CYPHER) >= {"handoff_breaks", "gaps", "overlaps_harmful", "overlaps_intentional"}
