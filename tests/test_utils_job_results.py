import pytest
from decimal import Decimal
from app.api.job_results import _safe_filename, _to_decimal

def test_safe_filename():
    assert _safe_filename(None) == "analysis-report"
    assert _safe_filename("") == "analysis-report"
    assert _safe_filename("test.pdf") == "test.pdf"
    assert _safe_filename("bad/\\name") == "bad-name"
    assert _safe_filename("..hidden") == "hidden"

def test_to_decimal():
    assert _to_decimal("10.5") == Decimal("10.5")
    assert _to_decimal(None) == Decimal("0")
    assert _to_decimal("bad") == Decimal("0")
    assert _to_decimal(5) == Decimal("5")
    assert _to_decimal(Decimal("2.2")) == Decimal("2.2")
