"""정책핏 인천 — 확정본(final).

`06_앱`의 검증된 엔진(추출·규칙·그래프)을 그대로 쓰고, 화면과 판정 축만
조사자 C의 C1 7개 성과축 기준으로 다시 짠다.
"""
import sys
from pathlib import Path

# 06_앱의 engine과 data를 재사용한다 — 검증된 것을 복사해 갈라놓지 않는다.
APP = Path(__file__).resolve().parent.parent.parent / "06_앱"
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))
