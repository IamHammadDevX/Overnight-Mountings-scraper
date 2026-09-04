from overnight_scraper.media import parse_color_media, with_color

def test_structured_media_parser():
    html = '<script id="product-images" type="application/json">["https://a/image.jpg"]</script><script id="product-videos" type="application/json">["https://a/video.mp4"]</script>'
    media = parse_color_media(html)
    assert media.images == ["https://a/image.jpg"]
    assert media.videos == ["https://a/video.mp4"]
    assert media.available is True

def test_color_replaces_only_color_parameter():
    assert with_color('https://example.test/p?metal=14+KT&color=White', 'Yellow').endswith('metal=14+KT&color=Yellow')

def test_static_alt_media_maps_to_colors():
    html = '''<script id="product-images" type="application/json">["https://a/base.jpg", "https://a/base.alt.jpg", "https://a/base.alt1.jpg"]</script><script id="product-videos" type="application/json">["https://a/base.video.white.mp4", "https://a/base.video.yellow.mp4", "https://a/base.video.rose.mp4"]</script>'''
    assert parse_color_media(html, "White").images == ["https://a/base.jpg"]
    assert parse_color_media(html, "Yellow").images == ["https://a/base.alt.jpg"]
    assert parse_color_media(html, "Rose").images == ["https://a/base.alt1.jpg"]
    assert parse_color_media(html, "Yellow").videos == ["https://a/base.video.yellow.mp4"]
    assert parse_color_media(html, "Rose").videos == ["https://a/base.video.rose.mp4"]

def test_unknown_alt_suffix_is_not_assigned():
    html = '''<script id="product-images" type="application/json">["https://a/base.alt2.jpg", "https://a/base.alt3.jpg", "https://a/base.alt4.jpg"]</script><script id="product-videos" type="application/json">[]</script>'''
    from overnight_scraper.media import unrecognized_color_media
    assert parse_color_media(html, "Yellow").images == []
    assert parse_color_media(html, "Rose").images == []
    assert unrecognized_color_media(html) == ["https://a/base.alt2.jpg", "https://a/base.alt3.jpg", "https://a/base.alt4.jpg"]

