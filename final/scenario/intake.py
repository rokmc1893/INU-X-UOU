"""입구 ②③ — 담당자가 직접 가져온 자료를 받는다.

A3 1단계 입력문서 중 두 가지에 해당한다.
  ② 정부 공모 안내문   — A4 사례2(K-NIBRT)가 여기서 출발했다
  ③ 기업/대학/현장 수요조사서

`fetch.fetch_policy_text()` → `extract.extract_card()`는 이미 있다. 여기서는 **넣는 길**만
만든다. 원문에 없는 값은 채우지 않고 `missing_fields`에 남기는 규칙은 그대로 지켜진다.

**올린 자료는 세션 한정이다.** 원장 파일을 덮어쓰지 않는다. 조사자가 확인한 원장과
담당자가 방금 올린 것을 섞으면 근거 등급이 무너지기 때문이다. 화면에서는 `직접 올림`
배지로 구분한다.
"""
import io
import re

from engine import extract, fetch

UPLOADED = "직접 올림"
MIN_CHARS = 120  # 이보다 짧으면 본문을 못 읽은 것으로 본다


class IntakeError(Exception):
    """왜 실패했는지 담당자가 읽을 수 있는 말로 담는다."""


def _new_id(kind, seq):
    return f"UP-{kind}-{seq:03d}"


def _finish(card, source, note, industry=None):
    card["data_type"] = UPLOADED
    card["_uploaded"] = True
    card["_intake_source"] = source
    card["evidence_status"] = "UPLOADED_UNVERIFIED"
    if industry and not card.get("strategic_industry"):
        card["strategic_industry"] = industry
    if not card.get("name"):
        card["name"] = f"(사업명 미확인 · {card['policy_id']})"
        card["_name_missing"] = True
    return card, note


def from_url(url, seq=1, industry=None, model="gpt-4o-mini"):
    """공고 주소를 넣으면 본문을 가져와 카드로 만든다."""
    url = (url or "").strip()
    if not re.match(r"^https?://", url):
        raise IntakeError("주소가 http:// 또는 https:// 로 시작해야 합니다.")
    try:
        text = fetch.fetch_policy_text(url)
    except Exception as e:
        raise IntakeError(
            "그 주소를 열지 못했습니다. 기관 누리집 중에는 보안 설정이 낡아 "
            f"바깥에서 못 여는 곳이 있습니다({type(e).__name__}). "
            "화면에서 본문을 복사해 「글로 붙여넣기」로 넣어 주세요.")
    if len(text) < MIN_CHARS:
        raise IntakeError(
            "주소는 열렸는데 본문이 거의 없습니다. 자바스크립트로 그리는 페이지일 수 있습니다. "
            "본문을 복사해 「글로 붙여넣기」로 넣어 주세요.")
    return _from_text(text, _new_id("URL", seq), url, industry, model)


def from_text(text, seq=1, industry=None, title=None, model="gpt-4o-mini"):
    """공고문·보고서 본문을 그대로 붙여넣는다. 비공개 문서를 옮겨 적을 때 쓴다."""
    text = (text or "").strip()
    if len(text) < MIN_CHARS:
        raise IntakeError(f"내용이 너무 짧습니다. 최소 {MIN_CHARS}자 이상 넣어 주세요.")
    head = f"# 제목: {title}\n" if title else ""
    return _from_text(head + text, _new_id("TXT", seq), "붙여넣은 글", industry, model)


def from_pdf(file_bytes, filename, seq=1, industry=None, model="gpt-4o-mini"):
    """PDF에서 글자를 뽑아 카드로 만든다.

    **스캔한 그림 PDF는 글자가 없어 실패한다.** 실제로 인천연구원 이슈&트렌드가 그랬다.
    실패를 조용히 넘기지 않고 왜 안 되는지 말해 준다.
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        raise IntakeError("이 환경에 PDF를 읽는 도구가 없습니다. 본문을 복사해 넣어 주세요.")
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        text = "\n".join((p.extract_text() or "") for p in reader.pages)
    except Exception as e:
        raise IntakeError(f"PDF를 여는 데 실패했습니다({type(e).__name__}).")
    if len(text.strip()) < MIN_CHARS:
        raise IntakeError(
            f"「{filename}」에서 글자를 뽑지 못했습니다. **사진으로 스캔한 문서**로 보입니다 — "
            "이런 파일은 글자가 아니라 그림이라 읽을 수 없습니다. "
            "원본 한글·워드 파일이 있으면 그것을 쓰거나, 필요한 대목을 옮겨 적어 주세요.")
    return _from_text(f"# 제목: {filename}\n{text}", _new_id("PDF", seq), filename,
                      industry, model)


def _from_text(raw, pid, source, industry, model):
    try:
        card = extract.extract_card(raw, pid, model=model)
    except Exception as e:
        # 열쇠가 없거나 호출이 막혀도 자료를 버리지 않는다 — 읽은 글은 남기고 판정만 미룬다.
        card = {"policy_id": pid, "name": _guess_title(raw), "summary": raw[:300],
                "missing_fields": ["전체 — 자동 정리 실패"], "_extract_failed": str(e)}
        return _finish(card, source,
                       "본문은 받았지만 자동 정리에 실패했습니다. "
                       "제목만 넣어 두었고 나머지 항목은 비어 있습니다.", industry)
    miss = card.get("missing_fields") or []
    note = ("원문에 적힌 것만 채웠습니다. "
            + (f"비어 있는 항목 {len(miss)}개는 원문에 없어서 그대로 두었습니다."
               if miss else "빠진 항목이 없습니다."))
    return _finish(card, source, note, industry)


def _guess_title(raw):
    for line in raw.splitlines():
        line = line.strip().lstrip("#").strip()
        if 4 <= len(line) <= 60:
            return line
    return None
