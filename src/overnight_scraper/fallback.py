from collections.abc import Callable
from .models import Attempt, Family, LookupOutcome

Lookup = Callable[[str], Attempt]

def find_family_source(family: Family, lookup: Lookup) -> Attempt:
    """Advance within a family only after confirmed product-not-found."""
    for sku in family.skus:
        attempt = lookup(sku)
        if attempt.family_id != family.family_id or attempt.sku != sku:
            raise ValueError("Lookup returned wrong family or SKU")
        if attempt.outcome is LookupOutcome.FOUND:
            return attempt
        if attempt.outcome is not LookupOutcome.NOT_FOUND:
            return attempt
    return attempt
