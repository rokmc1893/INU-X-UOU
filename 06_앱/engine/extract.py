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
1. 원문에 명시된 내용만 추출한다. 원문에 없는 필드는 null로 두고 missing_fields 배열에 필드명을 기록한다(기권).
2. source_span에는 각 추출 필드의 근거가 된 원문 문장을 **원문 그대로** 인용한다. 근거를 인용할 수 없는 필드는 추출하지 말고 기권한다.
3. stage는 다음 중 하나만: {stages}
4. occupation은 다음 어휘의 배열: {occupations}
5. linked_upstream/linked_downstream: 원문에 명시적으로 언급된 선행/후속 사업명 배열(없으면 []).
6. target은 {{"age_min": 숫자|null, "age_max": 숫자|null, "residency": 문자열|null, "employment_status": 문자열|null}}.

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
    """추출 계약 위반을 찾는다. 빈 리스트면 통과."""
    errors = []
    for f in NULLABLE_FIELDS:
        if card.get(f) is None and f not in card.get("missing_fields", []):
            errors.append(f"missing_fields: null 필드 '{f}'가 기권 기록에 없음")
    if card.get("stage") is not None and card["stage"] not in STAGES:
        errors.append(f"stage: '{card['stage']}'는 통제 어휘가 아님")
    for occ in card.get("occupation") or []:
        if occ not in OCCUPATIONS:
            errors.append(f"occupation: '{occ}'는 통제 어휘가 아님")
    tgt = card.get("target") or {}
    for k in TARGET_KEYS:
        if k not in tgt:
            errors.append(f"target: '{k}' 키 누락")
    nb = _norm(body)
    for field, quote in (card.get("source_span") or {}).items():
        if quote and _norm(quote) not in nb:
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
        card2["_validation_errors"] = validate_card(card2, body)
        return card2
    card["_validation_errors"] = []
    return card


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
