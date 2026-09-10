from pathlib import Path

from openpyxl import load_workbook

from overnight_scraper.fullsite import (
    FullSiteProduct,
    _finish,
    export_fullsite_workbook,
    extract_links,
)


def test_extract_links_keeps_product_and_page_urls():
    html = '''<a href="/product/foo">Product</a><a href="?page=2">Next</a><a href="https://outside.example/product/no">Outside</a>'''
    products, pages = extract_links(html, "https://www.overnightmountings.com/wedding_bands")
    assert products == {"https://www.overnightmountings.com/product/foo"}
    assert pages == {"https://www.overnightmountings.com/wedding_bands?page=2"}


def test_finish_prefers_complete_before_semi_mount():
    assert _finish("Semi-Mount and Complete") == "Complete"
    assert _finish("Semi Mount only") == "Semi-Mount"


def test_fullsite_export_is_standalone(tmp_path: Path):
    output = tmp_path / "fullsite.xlsx"
    export_fullsite_workbook([
        FullSiteProduct("https://example.test/p", "Wedding Bands", sku="SKU-1", price="123.45", white_images=["image"])
    ], output)
    workbook = load_workbook(output, read_only=True)
    try:
        sheet = workbook["Overnight Full Site"]
        rows = list(sheet.values)
    finally:
        workbook.close()
    assert rows[0][0] == "SKU"
    assert rows[1][0] == "SKU-1"
    assert '"0": "image"' in rows[1][rows[0].index("Images Link")]

def test_sku_uses_product_variants_json():
    from overnight_scraper.fullsite import product_from_html
    html = '''<script id="product-variants" type="application/json">[{"style_number":"85132-1/4","url":"ring-85132-1-4","parent_product":false},{"style_number":"85132-1","url":"ring-85132-1","parent_product":true}]</script><link rel="stylesheet">'''
    assert product_from_html("https://www.overnightmountings.com/product/ring-85132-1/", "Test", html).sku == "85132-1"

def test_product_html_never_uses_market_header_as_price():
    from overnight_scraper.fullsite import product_from_html
    product = product_from_html("https://www.overnightmountings.com/product/ring-85132-1/", "Test", "$4,400.80")
    assert product.price == ""
