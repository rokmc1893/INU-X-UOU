from engine.store import MemoryStore

CARD = {"policy_id": "P001", "name": "A사업", "stage": "교육훈련",
        "occupation": ["바이오생산"], "target": {"age_min": 18, "age_max": 39,
        "residency": "인천", "employment_status": None}, "data_type": "real"}
DEMAND = {"signal_id": "D001", "occupation": "바이오생산", "geography": "인천",
          "period": "2026", "value": "구인 120건", "source_url": "https://x", "data_type": "virtual"}

def test_memory_store_roundtrip():
    s = MemoryStore()
    s.load([CARD], [DEMAND])
    assert s.policies()[0]["policy_id"] == "P001"
    assert s.demands()[0]["signal_id"] == "D001"
    s.add_edges([{"src": "P001", "dst": "D001", "type": "COVERS", "props": {}}])
    assert s.edges()[0]["type"] == "COVERS"

def test_load_is_idempotent():
    s = MemoryStore()
    s.load([CARD], [])
    s.load([CARD], [])
    assert len(s.policies()) == 1
