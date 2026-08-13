"""원문 → 정책카드 JSON. LLM은 이 파일에만 존재한다 (스펙 §4)."""
import json
import re
from pathlib import Path

STAGES = ["교육훈련", "일경험", "구직지원", "매칭", "채용지원", "정착"]
OCCUPATIONS = ["바이오생산", "바이오품질", "SW·AI", "일반사무", "전직무"]

NULLABLE_FIELDS = ["name", "status", "owner_dept", "executor", "problem", "stage",
                   "intervention", "region", "application_period", "budget",
                   "output_kpi", "outcome_kpi"]
TARGET_KEYS = ["age_min", "age_max", "residency", "employment_status"]

PROMPT = """당신은 정책 원문에서 정책카드를 추출한다. 반드시 JSON 객체 하나만 출력한다.
규칙:
1. 원문에 명시된 내용만 추출한다. 원문에 없는 필드는 null로 두고 missing_fields 배열에 필드명을 기록한다(기권). **null인 모든 최상위 필드명을 missing_fields에 빠짐없이 나열하라.**
2. source_span의 키는 반드시 스키마 필드명(영문: name, stage, occupation, target, intervention 등)이고, 값은 근거가 된 원문 문장을 **원문에서 연속된 문자열 그대로 복사**한 것이다(요약·재구성·문장 결합 금지). 추출 필드는 근거를 인용할 수 없으면 추출하지 말고 기권한다. 분류 필드(stage·occupation)는 분류 근거 문장을 그대로 복사할 수 있을 때만 source_span에 넣고, 근거가 '직무 제한 언급의 부재'처럼 특정 문장이 아니면 **source_span에서 그 필드를 생략한다(분류값은 유지 — 기권 아님)**.
3. stage와 occupation은 **분류(코딩) 필드**다 — 원문에 해당 단어가 없어도 사업내용을 근거로 반드시 분류하고, source_span에 분류 근거 문장을 인용한다. 사업내용 자체를 알 수 없는 문서(계획 게시글 등)만 null로 기권한다.
   stage는 다음 중 하나만 ({stages}):
   - 교육훈련: 직무능력을 가르치는 교육·훈련 과정 (인턴십이 붙어 있어도 교육이 주면 교육훈련)
   - 일경험: 인턴·현장 체험이 주된 사업
   - 구직지원: 구직활동 지원 — 상담, 진로탐색, 역량강화 프로그램, 정장 대여, 활동비·응시료 지원
   - 매칭: 구인-구직 연결 — 취업스터디, 매칭 프로그램, 알선. 기관 운영비 지원 사업은 그 기관의 핵심 기능으로 분류한다(예: 대학일자리센터 운영 지원 → 매칭)
   - 채용지원: 기업에 주는 채용 인센티브·환경개선 지원
   - 정착: 채용 이후 근속·정착 지원
   - 인력 사슬 밖 사업(시설·인프라 구축, 기업 R&D 지원, 산업 육성 계획 등 사람의 취업 단계를 직접 다루지 않는 사업)은 stage를 null로 기권한다
4. occupation은 다음 어휘의 배열: {occupations}
   - occupation은 지원 자격이 아니라 **사업이 겨냥하는 직무**다. 지원대상이 "시민 누구나"여도 사업 내용이 특정 직무를 다루면 그 직무로 분류한다.
   - 교육·훈련 사업은 훈련 과정이 가르치는 내용으로 분류한다(예: 회계·인사·마케팅 실무 → 일반사무, AI·SW 개발 → SW·AI, 바이오 생산공정 → 바이오생산). 여러 직무를 가르치면 배열에 모두 넣는다.
   - 직무와 무관한 일반 지원(정장 대여, 활동비·응시료 지원, 상담, 매칭 일반)은 반드시 ["전직무"]로 기입한다. null 기권 금지 — 이것은 추측이 아니라 코딩 규칙이다.
5. linked_upstream/linked_downstream: 원문에 명시적으로 언급된 선행/후속 사업명 배열(없으면 []).
6. target은 {{"age_min": 숫자|null, "age_max": 숫자|null, "residency": 문자열|null, "employment_status": 문자열|null, "student_status": 문자열|null, "income_criteria": 문자열|null}}.
   - employment_status는 "미취업"/"재직"/null로 정규화, residency는 시·군·구 수준("인천" 등)으로 정규화한다.
   - student_status: 원문이 재학생 포함/제외를 명시하면 "재학생 포함" 또는 "재학생 제외", 언급 없으면 null.
   - income_criteria: 원문에 소득·재산 기준이 명시되면 원문 표현 그대로, 없으면 null. 이 두 필드는 대상 세분(의도적 중첩 판정)에 쓰인다.

스키마: {{"policy_id": "{pid}", "name", "status", "owner_dept", "executor", "problem",
"target", "stage", "occupation", "intervention", "region", "application_period",
"budget", "output_kpi", "outcome_kpi", "linked_upstream", "linked_downstream",
"source_span", "missing_fields"}}

원문:
{body}"""


def parse_meta(raw_text: str):
    """`# key: value` 헤더(`# ---`까지)와 본문을 분리한다."""
    meta, lines = {}, raw_text.splitlines()
    body_start = 0
    for i, line in enumerate(lines):
        if line.strip() == "# ---":
            body_start = i + 1
            break
        m = re.match(r"#\s*([\w_]+):\s*(.+)", line)
        if m:
            meta[m.group(1)] = m.group(2).strip()
    return meta, "\n".join(lines[body_start:]).strip()


def _norm(s: str) -> str:
    return re.sub(r"\s+", "", s)


def validate_card(card: dict, body: str) -> list:
    """추출 계약 위반을 찾는다. 빈 리스트면 통과. 형식 위반도 메시지로 만들어 재시도에 쓴다."""
    errors = []
    missing = card.get("missing_fields")
    if not isinstance(missing, list):
        errors.append("missing_fields: 배열(JSON array)이어야 함")
        missing = []
    for f in NULLABLE_FIELDS:
        if card.get(f) is None and f not in missing:
            errors.append(f"missing_fields: null 필드 '{f}'가 기권 기록에 없음")
    if card.get("stage") is not None and card["stage"] not in STAGES:
        errors.append(f"stage: '{card['stage']}'는 통제 어휘가 아님")
    occ_list = card.get("occupation")
    if occ_list is not None and not isinstance(occ_list, list):
        errors.append("occupation: 배열(JSON array)이어야 함")
        occ_list = []
    for occ in occ_list or []:
        if occ not in OCCUPATIONS:
            errors.append(f"occupation: '{occ}'는 통제 어휘가 아님")
    tgt = card.get("target")
    if tgt is not None and not isinstance(tgt, dict):
        errors.append("target: 객체(JSON object)여야 함")
        tgt = {}
    for k in TARGET_KEYS:
        if k not in (tgt or {}):
            errors.append(f"target: '{k}' 키 누락")
    span = card.get("source_span")
    if span is not None and not isinstance(span, dict):
        errors.append("source_span: {필드명: 원문 인용문} 형태의 객체(JSON object)여야 함")
        span = {}
    nb = _norm(body)
    for field, quote in (span or {}).items():
        if quote and _norm(str(quote)) not in nb:
            errors.append(f"source_span[{field}]: 인용문이 원문에 없음")
    return errors


def _openai_llm(model: str):
    from openai import OpenAI
    client = OpenAI()  # OPENAI_API_KEY는 .env → 환경변수로만
    def call(prompt: str) -> str:
        resp = client.chat.completions.create(
            model=model, temperature=0,
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.choices[0].message.content
    return call


def extract_card(raw_text: str, policy_id: str, llm=None, model: str = "gpt-4o-mini") -> dict:
    meta, body = parse_meta(raw_text)
    if llm is None:
        llm = _openai_llm(model)
    prompt = PROMPT.format(stages=STAGES, occupations=OCCUPATIONS, pid=policy_id, body=body)
    card = json.loads(llm(prompt))
    card["policy_id"] = policy_id
    card["source_url"] = meta.get("source_url")
    card["retrieved_at"] = meta.get("retrieved_at")
    card["data_type"] = meta.get("data_type", "real")
    errors = validate_card(card, body)
    if errors:  # 1회 재시도: 위반 내역을 프롬프트에 붙여 교정 요청
        retry = prompt + "\n\n이전 출력의 계약 위반:\n" + "\n".join(errors) + "\n위반을 수정한 JSON을 다시 출력하라."
        card2 = json.loads(llm(retry))
        card2.update({"policy_id": policy_id, "source_url": meta.get("source_url"),
                      "retrieved_at": meta.get("retrieved_at"),
                      "data_type": meta.get("data_type", "real")})
        _auto_repair(card2)
        card2["_validation_errors"] = validate_card(card2, body)
        return card2
    card["_validation_errors"] = []
    return card


def _auto_repair(card):
    """재시도 후에도 남은 '장부 기재' 위반만 기계적으로 닫는다.
    내용(추출값)은 건드리지 않는다 — null 필드를 missing_fields에 추가하는 것뿐."""
    mf = card.get("missing_fields")
    if not isinstance(mf, list):
        mf = []
    for f in NULLABLE_FIELDS:
        if card.get(f) is None and f not in mf:
            mf.append(f)
    card["missing_fields"] = mf


def main():
    """배치: data/policies/raw/*.txt → data/cards/P00N.json"""
    from dotenv import load_dotenv
    load_dotenv()
    base = Path(__file__).resolve().parent.parent / "data"
    out = base / "cards"
    out.mkdir(exist_ok=True)
    for txt in sorted((base / "policies" / "raw").glob("P*.txt")):
        pid = txt.stem.split("_")[0]
        card = extract_card(txt.read_text(encoding="utf-8"), pid)
        (out / f"{pid}.json").write_text(
            json.dumps(card, ensure_ascii=False, indent=2), encoding="utf-8")
        status = "OK" if not card["_validation_errors"] else f"위반 {len(card['_validation_errors'])}건"
        print(f"{pid}: {status}")


if __name__ == "__main__":
    main()
