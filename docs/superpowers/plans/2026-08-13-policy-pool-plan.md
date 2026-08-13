# 정책 풀·실시간 수집 구현 계획 (Phase 1~4)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 산업 선택→풀에서 정책 끌어오기(A), URL 실시간 수집(B), 풀 갱신 스크립트(업데이트 경로)를 오늘 밤 안에 앱에 추가한다.

**Architecture:** 스펙 `docs/superpowers/specs/2026-08-13-policy-pool-design.md` 참조. 기존 extract_card·detect·store를 재사용하고, 풀은 파일로 관리해 재실행 갱신이 가능하게 한다.

**Tech Stack:** 기존과 동일 + requests (URL 수집). HTML 파싱은 표준 lib `html.parser`.

## Global Constraints

- 마감 2026-08-14 08:00, 코어는 금일 중. API 키 노출 금지, `.env`만.
- B1 `UNKNOWN` → null 기권, `CONFLICTING:` 수치는 값으로 쓰지 않음, `evidence_status` 뱃지 필수.
- 기존 테스트 23건이 깨지면 안 됨. 각 태스크 끝에 `python -m pytest tests -q`.
- 경로 루트 `C:\workspace\uxi\06_앱\`.

---

## Phase 1 — A: 산업 선택 + 풀에서 끌어오기

### Task 1.1: engine/pool.py — B1 행 → 카드 변환

**Files:** Create `06_앱/engine/pool.py`, `06_앱/tests/test_pool.py`, Copy `data/pool/B1_policy_portfolio.csv` (스크래치패드에서)

**Interfaces:**
- `row_to_pseudo_source(row: dict) -> str` — B1 행을 `# key: value` 메타헤더 + 본문 텍스트로 변환. UNKNOWN → 해당 줄 생략, `CONFLICTING:` 값 → "출처 간 수치 충돌로 미기재" 문장으로 치환
- `convert_industry(industry: str, llm=None) -> list[dict]` — 해당 산업 행들을 extract_card로 변환, 카드에 `stable_policy_id`·`evidence_status`·`pool_version`(=version) 추가, `policy_id`=stable_policy_id
- CLI `python -m engine.pool 바이오` → `data/pool/cards/IC-*.json` 재생성 (= 백그라운드 갱신 진입점)

- [ ] Step 1: 테스트 작성 — `row_to_pseudo_source`가 UNKNOWN 줄을 생략하고 CONFLICTING을 치환하는지, `convert_industry`가 fake llm으로 카드에 stable_policy_id·evidence_status를 붙이는지
- [ ] Step 2: 실패 확인 → 구현 → 통과 확인
- [ ] Step 3: Commit `feat: engine/pool.py — B1 원장→카드 변환기(갱신 CLI)`

### Task 1.2: 바이오 풀 배치 변환 (실 API)

- [ ] Step 1: Run `python -X utf8 -m engine.pool 바이오` → 16건 (바이오 15 + 바이오+디지털데이터 1)
- [ ] Step 2: 눈검수 — IC-BIO-001 시설구축의 stage(해당 없으면 null 허용), IC-BIO-002 교육과정이 [바이오생산·바이오품질]·교육훈련인지, CONFLICTING 예산이 null인지
- [ ] Step 3: Commit `feat: 바이오 정책 풀 카드 16건 (근거등급 표시)`

### Task 1.3: app.py 산업 선택

- [ ] Step 1: 사이드바 `st.selectbox("분석 범위", ["청년일자리(기본)", "청년일자리 + 바이오"])`; init(scope)로 캐시 키 분리; 바이오 선택 시 `data/pool/cards/IC-*.json` 결합 로드
- [ ] Step 2: `label()` 확장 — evidence_status 뱃지: 📰 언론보도 기반, ⚠️ 수치 충돌, 없으면 기존 🟢/🟡. 화면 2 컬럼·화면 3 정책 목록에 그대로 적용. 화면 4 상단에 "현재 분석 범위" 표시
- [ ] Step 3: 브라우저 검증 — 바이오 선택 시 화면 2에 K-NIBRT 교육과정 등장 + 화면 3 바이오 공백이 커버로 바뀌고 인계 공백이 새로 표시되는지
- [ ] Step 4: Commit `feat: 산업 선택 — 풀에서 관련 정책 끌어오기`

## Phase 2 — B: URL 실시간 수집

### Task 2.1: engine/fetch.py

**Interfaces:** `fetch_policy_text(url: str, timeout=10) -> str` — requests.get → `html.parser` 기반 태그 제거·본문 추출 → `# source_url/retrieved_at/data_type: real` 메타헤더 붙인 텍스트. 실패 시 예외 그대로 전파(앱이 폴백 표시)

- [ ] Step 1: 테스트 — 고정 HTML 문자열로 파서 단위 테스트 (`_html_to_text`), 메타헤더 생성 테스트 (네트워크 불필요)
- [ ] Step 2: 실패 확인 → 구현(HTMLParser 서브클래스: script/style 무시, 블록태그 개행) → 통과
- [ ] Step 3: Commit `feat: engine/fetch.py — URL 정책 원문 수집기`

### Task 2.2: app.py URL 가져오기

- [ ] Step 1: 사이드바 expander "URL로 정책 가져오기": text_input + 버튼 → fetch → `extract_card(..., policy_id="U" + 순번)` → 카드 미리보기(st.json 축약) → "분석에 추가" 버튼 → `st.session_state.extra_cards`에 추가, findings 재계산은 session 카드 포함 버전으로
- [ ] Step 2: 실패 폴백 — `st.error("가져오기 실패 — 원문 텍스트를 data/policies/raw에 직접 넣어도 됩니다 (오류: ...)")`
- [ ] Step 3: 실 URL 1건(청년포털 사업 페이지)로 브라우저 검증
- [ ] Step 4: Commit `feat: URL 실시간 수집→추출→분석 추가`

## Phase 3 — 업데이트 경로 문서화 + 마무리

- [ ] Task 3.1: 결정로그 D-015 기록 (풀 구조·갱신 경로·근거등급 노출·예상 판정 변화 수용). README 또는 스펙에 "갱신 = `python -m engine.pool <산업>` 재실행, 스케줄러 등록은 운영 로드맵" 명시
- [ ] Task 3.2: 전체 pytest + 4화면+신기능 브라우저 최종 검증 + evaluate 재실행(기존 16건 지표 불변 확인) + 커밋·푸시

## Phase 4 — 발표자료 (별도 흐름)

- [ ] 데크 구성: 문제 재정의(D-001) → 데모 4화면 + 진입 흐름 → 검증 수치(v2→v6) → 데모/운영 아키텍처 2단(D-009·D-010) → 로드맵(자동 서칭·스케줄러·다산업)
- [ ] 시연 녹화 백업
