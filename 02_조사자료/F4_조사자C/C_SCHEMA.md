# SCHEMA — 조사자 C 데이터 정의서

데이터를 읽거나 쓰기 전에 이 문서를 확인한다. 통제어휘 밖의 값을 넣으면 채점·정답셋이 깨진다.

---

## 통제어휘 (전 파일 공통)

### match_status / final_status — 정책-예산 매칭 결과
| 값 | 정의 |
|---|---|
| `EXACT` | 정규화 후 완전일치 |
| `FUZZY` | 유사도 매칭(cutoff 0.72 이상), 부서명 대조로 오탐 필터링 완료 |
| `MATCH_국가직접` / `MATCH_부서개편` | 완전일치는 아니나 국가직접지원 표기 또는 부서명 변경으로 확정된 매칭 |
| `NOT_APPLICABLE_산하기관(...)` | 본청이 아니라 산하 공단·공사 소관이라 원장에 없는 게 정상 |
| `NOT_PUBLICLY_VERIFIABLE` | 원장·스냅샷 어디에도 없고, 국가직접·산하기관 여부를 전화 확인 없이는 못 좁힘 |
| `CONFIRMED_ABSENT` | 원장 전체(3,711건)를 문자열로 확인해 진짜로 없음을 확정(예: 로보컵) |
| `NEEDS_REVIEW` | 두 개 이상의 정책ID가 원장상 같은 항목에 매칭 — 원 소유자(B 등)의 원문 재확인 필요 |

> `NOT_PUBLICLY_VERIFIABLE`을 "예산이 없다"로 바꿔 쓰지 않는다. 국가직접·군구·산하기관 수행일 수 있다.

### evidence_status — B1에서 가져온 값 그대로 사용 (C9)
`PRIMARY_VERIFIED` / `SECONDARY_PRESS_ONLY` / `CONFLICTING_FIGURES` / `UNVERIFIED` — 정의는 B_SCHEMA.md 참조.

### verification_status — C9 전용, B1 예산 검증 결과
| 값 | 정의 |
|---|---|
| `RESOLVED` | 인천시 공식 예산 원장으로 B의 UNKNOWN·미확인 총액을 확정 |
| `PARTIALLY_RESOLVED` | 확정은 됐으나 B의 보도 수치와 성격이 다름(예: 총액 vs 연차배정) — 상충으로 취급하지 않음 |
| `NEEDS_REVIEW` | 원장상 다른 정책ID와 동일 항목에 매칭됨 — B 재확인 요청 |
| `CONFIRMED_ABSENT` | 원장 전체에 해당 문자열 없음 확정 |

### expected_label — C3 정답셋 전용
자유 텍스트이나 다음 계열을 우선 사용: `MATCH` / `NO_MATCH` / `OVERLAP_CANDIDATE` / `NOT_DUPLICATE` / `CONFLICTING_FIGURES` / `NOT_PUBLICLY_VERIFIABLE` / `SCALE_MISMATCH_FLAGGED` / `SCRUTINY_FLAGGED` / `NEEDS_REVIEW`

> `OVERLAP_CANDIDATE`를 "확정 중복"으로 시스템이 표시하면 안 된다. B가 명시한 대로 6대산업 스코프에서 확정 중복은 0건이다.

### mvp_status — C1 채점표 전용
`MVP 1순위(주 분석 모듈)` / `MVP 2순위(...)` / `상위 해석축` / `보조 시각화(...)` / `조건부 보류(...)` / `별도 조사(...)` / `장기 결과(제외)`

### score_by_criterion 8개 채점 기준과 가중치
| 기준 | 가중치 |
|---|---:|
| 공개데이터 가용성 | 15% |
| 정책·산업·지역·시점 연결성 | 15% |
| 정답·반례 구축 가능성 | 20% |
| 3일 성능검증 가능성 | 20% |
| 행정 의사결정 유용성 | 15% |
| 최신성·갱신 가능성 | 5% |
| 법·계약 위험의 낮음 | 5% |
| 장기 성과평가 확장성 | 5% |

> 점수는 근거(원문 파일명 또는 B/C 문서 섹션) 없이 부여하지 않는다.

---

## C1_outcome_feasibility_matrix.csv (7행)

| 컬럼 | 설명 |
|---|---|
| `rank` | 6대산업 점수 기준 순위 |
| `outcome` | 일곱 후보 중 하나(정책실효성저하/예산비효율/기업경쟁력약화/인재유출미스매치/산업생태계형성어려움/지역격차심화/정책신뢰도저하) |
| `scope` | 이 채점이 적용되는 코퍼스 — 현재는 전부 `6대 전략산업(B1 52건)` |
| `score_by_criterion` | 8개 기준 점수를 `약칭점수\|약칭점수...` 형식으로 압축 |
| `weighted_score_v3(6대산업)` | 가중합 |
| `weighted_score_v2(청년정책)` | 이전 스코프 점수 — 비교용 |
| `rationale` | 점수 근거. B1/B2/B3/B4 특정 섹션 또는 evidence ID(E-xx) 인용 |
| `mvp_status` | 통제어휘 참조 |
| `evidence_source` | 근거 파일 경로 |

## C3_gold_set.csv (22행 — scope 컬럼으로 6대산업 9건·청년정책 13건 구분)

| 컬럼 | 설명 |
|---|---|
| `case_id` | 고유 ID, 재사용 금지 |
| `test_type` | 사례 유형(역할중첩 후보/정보출처 상충/자료부족/오탐방지/중복의심/신뢰도판정/규모KPI불일치/음성사례) |
| `input_a` / `input_b` | 비교 대상 |
| `expected_label` | 통제어휘 참조 |
| `expected_evidence` | 판정 근거가 어느 파일·섹션에 있는지 |
| `accepted_alternative` | 허용되는 대안 라벨(없으면 `없음`) |
| `prohibited_claim` | 시스템이 하면 안 되는 과잉 주장 |
| `왜_이_사례인가` | 이 사례가 정답셋에 필요한 이유 |
| `source` | 원 출처(B4 섹션, B3 evidence_id, C9 등) |
| `reviewer_1` / `reviewer_2` | 독립 라벨링 담당자 — **현재 전부 PENDING, 팀원 1명의 실제 라벨링 필요** |
| `agreement_status` | `UNREVIEWED` / 라벨링 후 `AGREE` / `DISAGREE` |

> 정답셋 필수 5종류(명시적 KPI불일치·실제역할중첩·유사비중복음성·미확인정답·최신구자료충돌) 매핑은 `C_README.md`에 표로 정리돼 있다.

## C9_b1_budget_verification.csv (10행)

| 컬럼 | 설명 |
|---|---|
| `stable_policy_id` | B1의 ID 그대로 사용 |
| `policy_name` | B1의 정책명 |
| `B_reported_budget` / `B_evidence_status` | B1 원본 값 |
| `verification_status` | 통제어휘 참조 |
| `official_budget_won` | 인천시 예산 원장 확정액(원) |
| `official_dept` | 원장상 소관부서 |
| `official_source_line` | 원장상 세부사업명 |
| `note` | 검증 과정에서 발견한 특이사항 |

---

## 새 행을 추가할 때

1. `rationale`/`expected_evidence`/`note`에 원문 근거(파일명 또는 B의 evidence_id)가 있는가? 없으면 추가하지 않는다.
2. 통제어휘를 벗어난 값이 있는가? 없어야 한다.
3. `OVERLAP_CANDIDATE`나 `NEEDS_REVIEW`를 "확정"으로 바꿔 쓰지 않았는가?
4. C3라면 `prohibited_claim`을 채웠는가 — 이게 없으면 시스템이 어떤 과잉 주장을 막아야 하는지 알 수 없다.
5. 확인 못 한 값은 `UNKNOWN` 또는 `NOT_PUBLICLY_VERIFIABLE`로 둔다. 추정치를 넣지 않는다.
6. `C_README.md`의 변경 이력 절에 무엇을 왜 바꿨는지 남긴다.
