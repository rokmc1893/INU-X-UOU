# 정책핏 인천 — 앱

인천시 청년 일자리 정책 사이의 **지원 공백 · 인계 공백 · 조정 필요 중복 · 의도적 병행 · 보완 관계**를 규칙으로 판정해, 공무원의 「유사·중복 사업 자체 검토서」 **초안**을 만들어 주는 Streamlit 앱.
A3 워크플로우 3단계(타 부서 협의·유사·중복 검토)에서 주무관이 손으로 하던 **기존 사업 대조**를 자동화한다 — 검토서 서식까지 맞춘 것은 아니다.

판정은 전부 규칙이 한다. LLM은 정책 원문을 카드로 정규화하는 **추출 단계에만** 존재한다 (`engine/detect.py`에 `import openai`가 없다).

## 실행

```bash
cd 06_앱
pip install -r requirements.txt
cp .env.example .env      # OPENAI_API_KEY 입력
python -m streamlit run app.py
```

→ http://localhost:8501

**Neo4j는 없어도 된다.** 연결에 실패하면 동일 논리의 파이썬 규칙(`MemoryStore`)으로 자동 전환되고, 현재 스토어가 사이드바에 표시된다. Neo4j로 돌리려면:

```bash
docker compose up -d
```

**API 키가 없어도 앱은 뜬다.** 정책 카드(`data/cards/`)가 이미 추출·저장돼 있기 때문이다. 키는 화면 2의 라이브 재추출 버튼과 재추출 배치에만 필요하다.

## 인터넷도 앱도 없을 때 (발표장 폴백)

```bash
python -m engine.snapshot     # → data/demo_fallback.html
```

`data/demo_fallback.html`을 브라우저로 열면 4화면의 핵심 내용(사슬·판정·정확도)이 의존성 없이 그대로 나온다. 시연 실패 시 이것을 띄운다.

## 재현 명령

| 명령 | 결과 |
|---|---|
| `python -m pytest tests -v` | 테스트 36건 |
| `python -m engine.evaluate` | 정답셋 채점 → `data/results.json` (4지표) |
| `python -m engine.extract` | 원문 재추출 → `data/cards/*.json` (**API 호출·비용 발생**) |
| `python -m engine.pool 바이오` | 정책 풀 갱신 → `data/pool/cards/` (**API 호출**) |
| `python -m engine.export_cypher` | Neo4j 적재 스크립트 → `data/graph_load.cypher` |

풀 갱신은 이 명령 재실행이 전부다. 스케줄러에 걸면 백그라운드 업데이트가 되지만, 스케줄러 등록 자체는 운영 로드맵이며 지금 구현돼 있지 않다.

## 구조

```
app.py              4화면 Streamlit (검토 개요 / 연계 지도 / 검토표 / 조치 제안서)
engine/
  extract.py        원문 → 정책카드. LLM은 여기에만 있다. 기권 계약·인용 실재 검증 포함
  detect.py         규칙 5종 + 동일 논리 Cypher. 판정에 LLM 불개입
  store.py          Neo4jStore(주) + MemoryStore(자동 폴백)
  evaluate.py       정답셋 채점 → results.json
  pool.py           B1 정책원장 → 카드 변환 (산업 선택용 풀, 갱신 진입점)
  fetch.py          URL → 정책 원문 수집
  refdata.py        A1·A2·B2·B3 조사 원장 로더 (부서·달력·수요신호·연계근거의 단일 출처)
  export_cypher.py  Neo4j 적재 스크립트 생성
  snapshot.py       의존성 없는 정적 폴백 HTML 생성
```

## 데이터 출처와 한계

| 위치 | 내용 | 등급·한계 |
|---|---|---|
| `data/policies/raw/` | 인천청년포털 정책 원문 10건 | 실수집 (source_url·retrieved_at 포함) |
| `data/pool/` | F4 조사자 B의 정책원장 52건 → 바이오 16건 카드화 | **다수가 언론보도 2차 출처.** 카드에 `evidence_status` 표기. 인용은 원문이 아니라 원장 재구성 텍스트 기준 |
| `data/demand/` | 수요신호 5건 | **3건이 조사자 B의 B2 실신호(등급 B~D), 2건은 가상 표본.** 화면에 그대로 표기 |
| `data/pool/A1·A2·B2·B3` | 조사자 A·B 원장 사본 | `engine/refdata.py`가 읽는 **단일 출처**. 부서 연락처·예산 달력·수요신호·연계근거가 여기서 온다 |
| `data/gold/` | 자작 정답셋 37건 | **자기 채점이며 2인 교차판정 전 잠정치.** 독립 판정자 2차 대조는 `judge2_pass.csv` |

`data/results.json`의 수치를 인용할 때는 위 한계를 함께 표기한다. 원장(`05_발표자료/03_증거원장.csv`)에 없는 수치는 발표자료에 올리지 않는다.
