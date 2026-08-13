"""URL → 정책 원문 텍스트 수집기 (화면 B: 실시간 가져오기)."""
from datetime import date
from html.parser import HTMLParser


class _TextExtractor(HTMLParser):
    BLOCK = {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "table", "section"}
    SKIP = {"script", "style", "noscript"}

    def __init__(self):
        super().__init__()
        self.parts = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self._skip += 1
        elif tag in self.BLOCK:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip and data.strip():
            self.parts.append(data.strip() + " ")


def _html_to_text(html: str) -> str:
    p = _TextExtractor()
    p.feed(html)
    lines = [ln.strip() for ln in "".join(p.parts).splitlines()]
    return "\n".join(ln for ln in lines if ln)


def build_meta_header(url: str) -> str:
    return (f"# source_url: {url}\n"
            f"# retrieved_at: {date.today().isoformat()}\n"
            f"# data_type: real\n"
            f"# ---\n")


def fetch_policy_text(url: str, timeout: int = 10) -> str:
    """URL을 가져와 메타헤더 붙은 원문 텍스트로 반환. 실패 시 예외 전파(앱이 폴백 표시)."""
    import requests
    resp = requests.get(url, timeout=timeout,
                        headers={"User-Agent": "Mozilla/5.0 (policy-fit-incheon)"})
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding or resp.encoding
    return build_meta_header(url) + _html_to_text(resp.text)
