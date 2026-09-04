from overnight_scraper.fallback import find_family_source
from overnight_scraper.models import Attempt, Family, LookupOutcome

def test_fallback_advances_only_after_not_found():
    family = Family("FAM-1", "A", ("A", "B", "C"), 3)
    called = []
    def lookup(sku):
        called.append(sku)
        return Attempt("FAM-1", sku, None, LookupOutcome.NOT_FOUND if sku == "A" else LookupOutcome.FOUND)
    assert find_family_source(family, lookup).sku == "B"
    assert called == ["A", "B"]

def test_transient_error_does_not_advance_family():
    family = Family("FAM-1", "A", ("A", "B"), 2)
    called = []
    def lookup(sku):
        called.append(sku)
        return Attempt("FAM-1", sku, None, LookupOutcome.TRANSIENT_ERROR)
    assert find_family_source(family, lookup).outcome is LookupOutcome.TRANSIENT_ERROR
    assert called == ["A"]
