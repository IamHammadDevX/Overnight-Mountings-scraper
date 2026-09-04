from playwright.sync_api import sync_playwright
import json
url = "https://www.overnightmountings.com/product/men-s-oval-cabochon-gemstone-ring-10002-10x8/?color=White&finger_size=10.00&level=Polished&metal=14+KT"
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    events = []
    def record(response):
        request = response.request
        if request.resource_type in {"fetch", "xhr"} or "api" in request.url.lower():
            events.append({"url": request.url, "method": request.method, "resource_type": request.resource_type, "status": response.status, "post_data": request.post_data, "headers": dict(request.headers)})
    page.on("response", record)
    page.goto(url, wait_until="networkidle", timeout=60000)
    events.clear()
    page.locator('.color-option[data-value="Rose"]').click()
    page.wait_for_timeout(5000)
    print(json.dumps({"page_url_after_click": page.url, "events": events}, indent=2))
    browser.close()

