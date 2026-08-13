from engine.fetch import _html_to_text, build_meta_header

HTML = """<html><head><title>사업 안내</title><style>.x{color:red}</style>
<script>var a=1;</script></head>
<body><h1>테스트 사업</h1><p>지원대상: 인천 청년</p>
<div>사업내용: 교육 지원</div></body></html>"""

def test_html_to_text_strips_tags_and_scripts():
    text = _html_to_text(HTML)
    assert "테스트 사업" in text and "지원대상: 인천 청년" in text
    assert "var a=1" not in text and "color:red" not in text

def test_meta_header():
    head = build_meta_header("https://example.org/p")
    assert head.startswith("# source_url: https://example.org/p")
    assert "# data_type: real" in head and "# ---" in head
