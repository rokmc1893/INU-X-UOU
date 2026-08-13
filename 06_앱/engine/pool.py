"""B1 정책원장 행 → 정책카드 변환기.

`python -m engine.pool <산업>` 재실행이 곧 풀 갱신이다 — 스케줄러(작업 스케줄러/cron)에
걸면 백그라운드 업데이트가 된다 (스케줄러 등록 자체는 운영 로드맵).
"""
import csv
import json
import sys
from pathlib import Path

from engine.extract import extract_card

# B1 컬럼 → 의사원문 라벨. 순서대로 본문을 구성한다.
FIELD_LABELS = [
    ("status", "사업상태"),
    ("owner_department", "주관기관"),
    ("executor", "운영기관"),
    ("target", "지원대상"),
    ("problem", "해결하려는 문제"),
    ("intervention", "사업내용"),
    ("industry", "대상 산업"),
    ("occupation", "대상 직무"),
    ("skill", "다루는 기술"),
    ("geography", "사업 지역"),
    ("application_period", "신청기간"),
    ("delivery_period", "사업기간"),
    ("budget", "예산"),
    ("budget_source", "재원"),
    ("kpi", "성과지표"),
    ("reported_result", "보고된 실적"),
    ("upstream_policy", "선행 사업"),
    ("downstream_policy", "후속 사업"),
]


def row_to_pseudo_source(row: dict) -> str:
    """B1 행을 extract_card가 읽는 `# key: value` 메타헤더 + 본문 텍스트로 변환.

    UNKNOWN 값은 줄 자체를 생략(원문에 없음 = 기권 대상),
    `CONFLICTING:` 값은 수치를 쓰지 않고 충돌 사실만 남긴다 (B_README 금지사항).
    """
    first_url = (row.get("source_url") or "").split("|")[0].strip()
    lines = [
        f"# source_url: {first_url}",
        f"# retrieved_at: {row.get('version', '')}",
        "# data_type: real",
        "# ---",
        f"# {row.get('policy_name', '')}",
        "",
    ]
    for key, label in FIELD_LABELS:
        v = (row.get(key) or "").strip()
        if not v or v == "UNKNOWN" or "UNKNOWN" in v:
            continue
        if v.startswith("CONFLICTING"):
            lines.append(f"{label}: 출처 간 수치 충돌로 미기재")
            continue
        lines.append(f"{label}: {v}")
    return "\n".join(lines)


def load_rows(industry: str = None) -> list:
    path = Path(__file__).resolve().parent.parent / "data" / "pool" / "B1_policy_portfolio.csv"
    with open(path, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if industry:
        rows = [r for r in rows if industry in (r.get("strategic_industry") or "")]
    return rows


def convert_industry(industry: str, llm=None, rows=None) -> list:
    if rows is None:
        rows = load_rows(industry)
    cards = []
    for row in rows:
        text = row_to_pseudo_source(row)
        card = extract_card(text, row["stable_policy_id"], llm=llm)
        card["stable_policy_id"] = row["stable_policy_id"]
        card["evidence_status"] = row.get("evidence_status", "")
        card["pool_version"] = row.get("version", "")
        card["strategic_industry"] = row.get("strategic_industry", "")
        cards.append(card)
    return cards


def main():
    from dotenv import load_dotenv
    load_dotenv()
    industry = sys.argv[1] if len(sys.argv) > 1 else "바이오"
    out = Path(__file__).resolve().parent.parent / "data" / "pool" / "cards"
    out.mkdir(parents=True, exist_ok=True)
    cards = convert_industry(industry)
    for c in cards:
        (out / f"{c['policy_id']}.json").write_text(
            json.dumps(c, ensure_ascii=False, indent=2), encoding="utf-8")
        status = "OK" if not c.get("_validation_errors") else f"위반 {len(c['_validation_errors'])}건"
        print(f"{c['policy_id']}: {status} [{c.get('evidence_status', '')}]")
    print(f"{len(cards)}건 → data/pool/cards/ (재실행하면 갱신)")


if __name__ == "__main__":
    main()
