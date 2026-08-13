import json
from engine.pool import row_to_pseudo_source, convert_industry

ROW = {
    "stable_policy_id": "IC-BIO-999", "version": "2026-08-13",
    "strategic_industry": "바이오", "policy_name": "테스트 바이오 교육",
    "status": "운영", "owner_department": "보건복지부",
    "executor": "연세대 K-NIBRT사업단", "target": "예비취업자",
    "problem": "바이오공정 인력 부족", "intervention": "실습형 교육과정 운영",
    "industry": "바이오의약품 제조", "occupation": "생산/공정/QA/QC",
    "skill": "배양-정제-분석", "geography": "연수구 송도",
    "application_period": "수시", "delivery_period": "2021~",
    "budget": "CONFLICTING: 677억 vs 434억", "budget_source": "UNKNOWN",
    "kpi": "연 2,000명", "reported_result": "누적 881명(2023 시점)",
    "upstream_policy": "UNKNOWN", "downstream_policy": "",
    "source_url": "http://example.org/a | http://example.org/b",
    "evidence_status": "SECONDARY_PRESS_ONLY",
}

def test_pseudo_source_skips_unknown_and_masks_conflicting():
    text = row_to_pseudo_source(ROW)
    assert "# source_url: http://example.org/a" in text  # 첫 URL만
    assert "UNKNOWN" not in text                          # UNKNOWN 줄 생략
    assert "677억" not in text                            # 충돌 수치 미기재
    assert "출처 간 수치 충돌로 미기재" in text
    assert "실습형 교육과정 운영" in text

def test_convert_industry_attaches_pool_fields():
    def fake(prompt):
        return json.dumps({
            "policy_id": "IC-BIO-999", "name": "테스트 바이오 교육", "status": "운영",
            "owner_dept": "보건복지부", "executor": "연세대 K-NIBRT사업단",
            "problem": "바이오공정 인력 부족",
            "target": {"age_min": None, "age_max": None, "residency": None,
                       "employment_status": None, "student_status": None,
                       "income_criteria": None},
            "stage": "교육훈련", "occupation": ["바이오생산", "바이오품질"],
            "intervention": "실습형 교육과정 운영", "region": "인천 송도",
            "application_period": "수시", "budget": None,
            "output_kpi": "연 2,000명", "outcome_kpi": None,
            "linked_upstream": [], "linked_downstream": [],
            "source_span": {"intervention": "실습형 교육과정 운영"},
            "missing_fields": ["budget", "outcome_kpi"],
        }, ensure_ascii=False)
    cards = convert_industry("바이오", llm=fake, rows=[ROW])
    assert len(cards) == 1
    c = cards[0]
    assert c["policy_id"] == "IC-BIO-999"
    assert c["stable_policy_id"] == "IC-BIO-999"
    assert c["evidence_status"] == "SECONDARY_PRESS_ONLY"
    assert c["pool_version"] == "2026-08-13"
