from pathlib import Path
from tempfile import TemporaryDirectory

from overnight_scraper.models import ColorMedia, Family, FamilyResult
from overnight_scraper.storage import connect, init_db, pending_family_ids, save_result, seed_families


def test_terminal_result_is_skipped_on_resume():
    with TemporaryDirectory() as directory:
        family = Family("FAM-X", "SKU-X", ("SKU-X",), 1)
        db = Path(directory) / "scraper.db"
        connection = connect(db)
        try:
            init_db(connection)
            seed_families(connection, [family])
            assert pending_family_ids(connection) == {"FAM-X"}
            save_result(
                connection,
                FamilyResult(
                    family_id="FAM-X",
                    source_sku="SKU-X",
                    product_url="https://example.test/product/x",
                    white=ColorMedia(["white.jpg"], [], True, {"color_specific": True}),
                    yellow_gold=ColorMedia([], [], True, {"color_specific": False}),
                    rose_gold=ColorMedia([], [], True, {"color_specific": False}),
                ),
            )
            assert pending_family_ids(connection) == set()
        finally:
            connection.close()
