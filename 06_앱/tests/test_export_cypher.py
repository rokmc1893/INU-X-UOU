from engine.export_cypher import export_cypher

def test_export_contains_create_statements():
    cards = [{"policy_id": "P1", "name": "A", "stage": "교육훈련", "occupation": ["전직무"],
              "target": {"age_min": 18, "age_max": 39, "residency": None,
                         "employment_status": None}}]
    demands = [{"signal_id": "D1", "occupation": "바이오생산", "geography": "인천",
                "period": "2026", "value": "v", "data_type": "virtual"}]
    edges = [{"src": "P1", "dst": "D1", "type": "COVERS", "props": {}}]
    text = export_cypher(cards, demands, edges)
    assert "CREATE (:Policy" in text and "CREATE (:Demand" in text
    assert "COVERS" in text and "P1" in text
