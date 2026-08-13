import json
from engine.extract import parse_meta, validate_card, extract_card, STAGES

RAW = """# source_url: https://example.org/p
# publisher: 인천광역시
# retrieved_at: 2026-08-13
# data_type: real
# ---
# 테스트사업 안내
지원대상: 인천시 거주 18세~39세 청년
사업내용: 실무 교육훈련 3개월
"""

def make_card(**over):
    card = {
        "policy_id": "P999", "name": "테스트사업", "status": None,
        "owner_dept": None, "executor": None, "problem": None,
        "target": {"age_min": 18, "age_max": 39, "residency": "인천", "employment_status": None},
        "stage": "교육훈련", "occupation": ["전직무"], "intervention": "실무 교육훈련 3개월",
        "intervention_type": "교육훈련",
        "region": "인천", "application_period": None, "budget": None,
        "output_kpi": None, "outcome_kpi": None,
        "linked_upstream": [], "linked_downstream": [],
        "source_span": {"intervention": "실무 교육훈련 3개월"},
        "missing_fields": ["status", "owner_dept", "executor", "problem",
                           "application_period", "budget", "output_kpi", "outcome_kpi"],
    }
    card.update(over)
    return card

def test_parse_meta():
    meta, body = parse_meta(RAW)
    assert meta["source_url"] == "https://example.org/p"
    assert meta["data_type"] == "real"
    assert body.startswith("# 테스트사업")

def test_validate_ok():
    _, body = parse_meta(RAW)
    assert validate_card(make_card(), body) == []

def test_validate_null_not_abstained():
    _, body = parse_meta(RAW)
    bad = make_card(missing_fields=[])  # null 필드가 있는데 기권 기록 없음
    assert any("missing_fields" in v for v in validate_card(bad, body))

def test_validate_span_not_in_source():
    _, body = parse_meta(RAW)
    bad = make_card(source_span={"intervention": "원문에 없는 문장"})
    assert any("source_span" in v for v in validate_card(bad, body))

def test_validate_bad_stage():
    _, body = parse_meta(RAW)
    bad = make_card(stage="자유텍스트")
    assert any("stage" in v for v in validate_card(bad, body))

def test_extract_card_with_fake_llm():
    fake = lambda prompt: json.dumps(make_card(), ensure_ascii=False)
    card = extract_card(RAW, "P999", llm=fake)
    assert card["policy_id"] == "P999"
    assert card["source_url"] == "https://example.org/p"
    assert card["data_type"] == "real"
    assert card["stage"] in STAGES
