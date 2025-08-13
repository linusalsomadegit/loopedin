


import threading
import time
import datetime
from urllib.parse import urldefrag

from webmonitor.Config import Config
from webmonitor.Scraper import get_site_html, save_html_to_file, get_site_links

class _Scheduler:
    def __init__(self):
        self.running = False
        self._thread = None
        self._lock = threading.Lock()

    def start(self):
        with self._lock:
            if not self.running:
                self.running = True
                if self._thread is None or not self._thread.is_alive():
                    self._thread = threading.Thread(target=self.worker_thread, daemon=True)
                    self._thread.start()

    def stop(self):
        with self._lock:
            self.running = False

    def worker_thread(self):
        while True:
            with self._lock:
                if not self.running:
                    # Wait until running is set again
                    time.sleep(0.1)
                    continue
            
            # Do work here
            print("Worker thread is active.")
            print("reading config")

            cfg = Config.read()
            if (not cfg):
                print("List of websites to scrape is empty. Doing nothing")
                continue

            # getting site info
            for next_website in cfg:
                start_web_scrape(next_website)

            # website_info = cfg[0]
            # print("Querying", website_info['url'])
            
            # site_html = get_site_html(website_info['url'])
            # alinks = get_site_links(site_html) # get the a links
            
            
            # print("NAME", website_info['name'])
            # save_html_to_file(sitedata, 'test.html')


            print("Trying again in 10 seconds")
            time.sleep(10)

    def start_web_scrape(self, website_info, max_iterations=3):
        """
        Starts the recursive scraping process from the base URL.
        Returns an object with base_url, job_name, scraped dict, and timestamp when finished.
        """
        base_url = website_info['url']
        ignore_list = website_info['ignoreList']
        job_name = website_info['name']

        scraped = {}
        explored = set()

        def recursively_scrape(url, iteration):
            url, _ = urldefrag(url)  # remove #fragment
            if iteration > max_iterations or url in explored:
                return

            explored.add(url)
            try:
                html = get_site_html(url)
                if not html:
                    print(f"[WARN] No HTML returned for {url}")
                    return
            except Exception as e:
                print(f"[ERROR] Failed to fetch {url}: {e}")
                return

            print("Setting", url, "to", html[:20])
            scraped[url] = html
            links = get_site_links(html, base_url)

            for link in links:
                if link not in explored and link not in ignore_list:
                    recursively_scrape(link, iteration + 1)

        recursively_scrape(base_url, 1)
        finished_at = datetime.datetime.now().isoformat()

        print(scraped.keys())

        return {
            "base_url": base_url,
            "job_name": job_name,
            "scraped": scraped,
            "finished_at": finished_at
        }



# Create a single instance
Scheduler = _Scheduler()
