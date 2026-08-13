from engine.evaluate import score

CARDS = {"P1": {"policy_id": "P1", "stage": "교육훈련", "budget": None,
                "target": {"age_min": 18, "age_max": 39, "residency": None,
                           "employment_status": None},
                "missing_fields": ["budget"],
                "source_span": {"stage": "실무 교육훈련"},
                "_span_check": {"stage": True}}}

def test_field_accuracy():
    gold = [{"case_id": "G1", "policy_id": "P1", "check_type": "field",
             "field": "stage", "gold_value": "교육훈련"},
            {"case_id": "G2", "policy_id": "P1", "check_type": "field",
             "field": "target.age_min", "gold_value": "18"},
            {"case_id": "G3", "policy_id": "P1", "check_type": "field",
             "field": "target.age_max", "gold_value": "40"}]  # 오답 1
    r = score(CARDS, gold, {"overlaps_harmful": [], "overlaps_intentional": []})
    assert abs(r["field_accuracy"] - 2 / 3) < 1e-9

def test_abstention_accuracy():
    gold = [{"case_id": "G1", "policy_id": "P1", "check_type": "abstention",
             "field": "budget", "gold_value": ""}]  # 기권이 정답 → 카드도 기권함
    r = score(CARDS, gold, {"overlaps_harmful": [], "overlaps_intentional": []})
    assert r["abstention_accuracy"] == 1.0

def test_overlap_label():
    gold = [{"case_id": "G1", "policy_id": "P1:P2", "check_type": "overlap_label",
             "field": "", "gold_value": "intentional"}]
    detect = {"overlaps_harmful": [],
              "overlaps_intentional": [{"items": ["P1", "P2"], "reason": "r"}]}
    r = score(CARDS, gold, detect)
    assert r["overlap_correct_rate"] == 1.0
