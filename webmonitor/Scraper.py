
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import requests


def get_site_html(website):
    # makes requests and returns html
    headers = {
        "User-Agent": "WebsiteMonitorBot/1.0 (+https://monitor.tool/info)"
    }
    
    try:
        response = requests.get(website, headers=headers, timeout=10)
        response.raise_for_status()  # Raises HTTPError for 4xx/5xx responses
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to retrieve {website}: {e}")
        return None

def save_html_to_file(html_text, filename="site_snapshot.html"):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html_text)
        print(f"[INFO] HTML saved to {filename}")
    except Exception as e:
        print(f"[ERROR] Failed to save HTML: {e}")


def get_site_links(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    parsed_base = urlparse(base_url)
    base_domain = parsed_base.netloc

    links = set()  # using a set to avoid duplicates

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"].strip()

        # Ignore empty, fragment-only, or javascript links
        if not href or href.startswith("#") or href.lower().startswith("javascript:"):
            continue

        # Convert to absolute URL
        full_url = urljoin(base_url, href)
        parsed_url = urlparse(full_url)

        # Keep only links within the same domain
        if parsed_url.netloc == base_domain:
            links.add(full_url)

    return list(links)
    