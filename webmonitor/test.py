import os
from webmonitor.Scraper import get_site_links

def read_test_html():
    test_html_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "test.html")
    with open(test_html_path, "r", encoding="utf-8") as f:
        return f.read()

def test_get_site_links():
    html = read_test_html()
    base_url = "https://www.vorne.com/"
    links = get_site_links(html, base_url)
    print("Extracted links:")
    for link in links:
        print(link)

from webmonitor.Scheduler import Scheduler

def test_start_web_scrape():
    website_info = {
        "name": "Vorne Industries",
        "url": "https://www.vorne.com/",
        "ignoreList": []
    }
    result = Scheduler.start_web_scrape(website_info, max_iterations=2)
    
    # Truncate html text values for display
    print("Scrape Job Result:")
    for k, v in result.items():
        if k == "scraped":
            print("scraped:")
            for url, html in v.items():
                snippet = html[:100].replace("\n", " ") + ("..." if len(html) > 100 else "") if html else "<None>"
                print(f"  {url}: {snippet}")
        else:
            print(f"{k}: {v}")

if __name__ == "__main__":
    test_start_web_scrape()

