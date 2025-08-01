import requests
import shutil
import queue
import json
import csv
import re
import os
import pickle
#   from torrequests import torrequests
#   if we're doing it the hard way :)
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import NoSuchElementException
#   from selenium.webdriver.chrome.webdriver import webdriver as ChromeDriverManager
from selenium.webdriver.chrome.service import Service # as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.devtools.v138 import network
from selenium.webdriver.common.devtools.v138 import event_breakpoints
import time
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from pathlib import Path
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, Text
from sqlalchemy.orm import sessionmaker
from collections import Counter
from urllib.parse import urlparse, parse_qs, urljoin


driver = None


def is_logged_in(driver):
    try:
        # Try finding the profile nav button
        driver.find_element(By.ID, "profile-nav-item")  # older
        return True
    except NoSuchElementException:
        try:
                # Try modern alternative
            driver.find_element(By.XPATH, "//img[contains(@class, 'global-nav__me-photo')]")
            return True
        except NoSuchElementException:
            return False
                
def clear():
            os.system('cls' if os.name == 'nt' else 'clear')

def get_width():
    try:
        return shutil.get_terminal_size().columns
    except:
        return 80


def wide():
    ascii_big = f"""
\033[1| _                               _\033[1;36m _       _ \033[0m
\033[1|| |    ___   ___  _ __   ___  __| \033[1;36m(_)_ __ | |\033[0m
\033[1|| |   / _ \ / _ \| '_ \ / _ \/ _`\\\033[1;36m| | '_ \| |\033[0m
\033[1|| |__| (o) | (O) | |_) |  __/ (_| \033[1;36m| | | | |_|\033[0m
\033[1||_____\___/ \___/| .__/ \___|\__,_\033[1;36m|_|_| |_(_)\033[0m
\033[1          \*****/  |_|             \033[1;36m             \033[0m                
    """
    print(ascii_big)

def medium():   #   use this for medium size but 
                #   probably not necessary since 
                #   ppl will either use either large or
                #   small cli
    ascii_big = f"""
\033[1| _                               _\033[1;36m _       _ \033[0m
\033[1|| |    ___   ___  _ __   ___  __| \033[1;36m(_)_ __ | |\033[0m
\033[1|| |   / _ \ / _ \| '_ \ / _ \/ _`\\\033[1;36m| | '_ \| |\033[0m
\033[1|| |__| (o) | (O) | |_) |  __/ (_| \033[1;36m| | | | |_|\033[0m
\033[1||_____\___/ \___/| .__/ \___|\__,_\033[1;36m|_|_| |_(_)\033[0m
\033[1          \*****/  |_|             \033[1;36m             \033[0m                
    """
    print(ascii_big)

def small():
    ascii_small = f"""
    Scrapeyou! (why is your terminal so small?!)
    """

def print_art():
    width = get_width()
    if width >= 100:
        wide()
    elif width >= 60:
        medium()
    else:
        small()


class Person:

    global driver
    
    def __init__(self, url):
        
        self.url = url
        self.profile_id = self.get_profile_id()
        self.query_ids = self.get_query_ids()
        self.session = self.create_session()
        self.all_data = self.get_all_data()
        self.scope = self.determine_scope()
        self.name = self.get_name()
        self.headline = self.get_headline()
        self.location = self.get_location()
        self.about = self.get_about()
        self.jobs = self.get_jobs()
        self.schools = self.get_schools()
        self.phone = self.get_phone()
        self.email = self.get_email()
        self.keywords = self.get_keywords()
        #   self.websites = self.get_websites()
        #   self.followers = self.get_followers()
        #   self.connections = self.get_connections()
        self.bday = self.get_bday()
        self.related_ppl = self.get_related_ppl()
            
    def get_profile_id(self):
        driver.get(self.url)
        time.sleep(5)
        html = driver.page_source
        match = re.search(r'"entityUrn":"urn:li:fsd_profile:(.*?)"', html)
        return match.group(1) if match else None

    def get_query_ids(self):
        logs = driver.get_log("performance")
        query_ids = {}

        for entry in logs:
            try:
                msg = json.loads(entry["message"])["message"]
                if msg["method"] == "Network.requestWillBeSent":
                    url = msg["params"]["request"]["url"]
                    if "voyager/api/graphql" in url and "queryId=" in url:
                        parts = url.split("queryId=")
                        qid = parts[1].split("&")[0]
                        if qid not in query_ids:
                            query_ids[qid] = url
                    
            except Exception:
                continue

        return query_ids

    def create_session(self):
        session = requests.Session()
        
        session.cookies['li_at'] = "AQEDATf5D_XXXXXXXXXXXXXXu"
        session.cookies["JSESSIONID"] = "ajax:1XXXXXXXXXXXXXX0"

        for cookie in driver.get_cookies():
            session.cookies.set(cookie['name'], cookie['value'])

        session.headers.update({
            "x-restli-protocol-version": "2.0.0",
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json"
        })
        session.headers["csrf-token"] = session.cookies["JSESSIONID"].strip('"')

        return session
        
    def get_all_data(self):

        all_data = {}

        for query_id in self.query_ids:

            voyager_url = f= (
                "https://www.linkedin.com/voyager/api/graphql?"
                f"queryId={query_id}"
                f"&variables=(profileUrn:urn%3Ali%3Afsd_profile%3A{self.profile_id})"
            )
                    
            response = self.session.get(voyager_url)
            if response.status_code == 200:
                print(f"[INFO] successfully fetched data for query url {voyager_url}")
                data = response.json()
                all_data[query_id] = data
            else:
                print(f"[ERROR] failed to fetch data for queryid {query_id} - status: {response.status_code}")
        
            return all_data

    def determine_scope(self):
        scope = []

        for query_data in self.all_data.values():
            if "included" in query_data:
                for obj in query_data["included"]:
                    urn = obj.get("entityUrn", "")
                    if f"fsd_profile:{self.profile_id}" in urn:
                        scope.append(obj)

        return scope

    def get_name(self):
        for obj in self.scope:
            if obj.get("firstName") or obj.get("lastName"):
                return f"{obj.get('firstName', '')} {obj.get('lastName', '')}".strip()
        return None

    def get_headline(self):
        for obj in self.scope:
            if "headline" in obj:
                return obj["headline"]
        return None

    def get_location(self):
        
        return None

    def get_about(self):
        #   FIX THIS ALSO
        for obj in self.scope:
            if "headline" in obj:
                return obj["headline"]
        return None

    def get_jobs(self):
        
        return None

    def get_schools(self):
        
        return None

    def get_phone(self):
        for obj in self.scope:
            if "headline" in obj:
                return obj["headline"]
        return None

    def get_email(self):
        for obj in self.scope:
            if "headline" in obj:
                return obj["headline"]
        return None

    def get_bday(self):
        for obj in self.scope:
            if "headline" in obj:
                return obj["headline"]
        return None

    def get_related_ppl(self):
        related = set()
        for query_data in self.all_data.values():
            if "included" in query_data:
                for obj in query_data["included"]:
                    if obj.get("entityUrn", "").startswith("urn:li:fsd_profile:") and "publicIdentifier" in obj:
                        pid = obj["publicIdentifier"]
                        if pid != self.profile_id:
                            related.add(f"https://www.linkedin.com/in/{pid}/")
        return list(related)

    def get_keywords(self):
        return None

    
class Spider:

    def __init__(self, url, parsedorders, engine):
        self.engine = engine
        self.qdppl = queue.Queue()
        self.parsedorders = parsedorders
        if url is not None:
            self.qdppl.put(url)
        self.tally = 0
        self.seen = set()
        self.stopat = parsedorders.scrape_limit 
        if self.tally == 0:
            self.loadlastqueue()
        if self.qdppl.empty() and self.parsedorders.uselastscrape:
            Help().emptylistgiven()
        self.recurse()
         
    def recurse(self):
        while not self.qdppl.empty() and self.tally < self.stopat:
            current_url = self.qdppl.get()
            if current_url in self.seen:
                continue
            self.seen.add(current_url)

            try:
                person = Person(current_url)

                self.tally += 1

                Rambling(person, self.tally, self.parsedorders, self.stopat, self.qdppl, self.engine)

                for new_url in person.related_ppl:  
                    if new_url not in self.seen:    
                        self.seen.add(new_url)
                        self.qdppl.put(new_url)    
            except Exception as e:                  
                #   if self.tally > 0:
                print(f"error scraping {current_url}: {e}")
        
    def loadlastqueue(self, filename="rollingurls.csv"):
        if self.parsedorders.uselastscrape:                 # and self.qdppl == None:
            with open(filename, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("http"):
                        self.qdppl.put(line)

            with open(filename, 'w', encoding='utf-8') as f:
                pass
            return self.qdppl

    
class Rambling:
    
    def __init__(self, person, tally, parsedorders, stopat, qdppl, engine):
        self.parsedorders = parsedorders
        self.stopat = stopat
        self.engine = engine
        self.person = person
        self.tally = tally
        self.qdppl = qdppl
            
        if self.parsedorders.printcount:
            clear()
            print(f"person # in search: \033[1;36m{self.tally}\033[0m")

        if self.parsedorders.printbasic:
            self.printbasic()

        if self.parsedorders.printextra:
            self.printextra()

        if self.parsedorders.csvout:
            self.export_csv()

        if self.parsedorders.tursoout:
            self.export_turso()

        if self.stopat == self.tally:
            self.scrape_finished()
        
    def printbasic(self):
        print(f"\nurl: {self.person.url}")
        print(f"\nname: {self.person.name}")
        print(f"\nheadline: {self.person.headline}")
        print(f"\location: {self.person.location}")
        print(f"\nabout: {self.person.about}")
        print(f"\njobs: {self.person.jobs}")
        print(f"\nschools: {self.person.schools}")
        print(f"\phone: {self.person.phone}")
        print(f"\nemail: {self.person.email}")
        print(f"\nkeywords: {self.person.keywords}")
        
    def printextra(self):
        print(f"\nwebsites: {self.person.websites}")
        print(f"\nfollowers: {self.person.followers}")
        print(f"\nconnections: {self.person.connections}")
        print(f"\nbday: {self.person.bday}")
        print(f"\nrelated_people: {self.person.related_ppl}")
       
        
    def export_csv(self, filename="output.csv"):

        with open(filename, mode='a', newline='', encoding='utf-8') as csvfile:
            if self.person is not None:
                writer = csv.writer(csvfile)

                if self.parsedorders.savebasic:
                    writer.writerow([
                        self.person.url,
                        self.person.name,
                        self.person.headline,
                        self.person.location,
                        self.person.about,
                        self.person.jobs,
                        self.person.schools,
                        self.person.phone,
                        self.person.email,
                        self.person.keywords
                    ])
                    
                if self.parsedorders.saveextra:
                    writer.writerow([
                        self.person.websites,
                        self.person.followers,
                        self.person.connections,
                        self.person.bday,
                        self.person.related_ppl
                    ])

                if self.tally == 0:
                    if self.parsedorders.savebasic:
                        basic = """"""
                        writer.writerow(basic)
                    if self.parsedorders.saveextra:
                        extra = """"""

    def scrape_finished(self):
        #   clear()
        print(f"\n")
        print(f"scrape complete!")
        print(f"\n")
        print(f"thank you for using")
        print_art()
        pickle.dump(driver.get_cookies(), open("linkedin_cookies.pkl", "wb"))
        if self.parsedorders.savethisscrape == True:
            self.save_urls()
        exit(0)
    
    def export_turso(self):
        if parsedorders.savebasic:
            try:
                values = {
                    
                }
        
                with self.engine.begin() as conn:
                    conn.execute(ppl_table.insert().values(**values))
        
            except Exception as e:
                if self.parsedorders.printbasic or self.parsedorders.printextra or self.parsedorders.printcount:
                    print(f"\033[1;31mWARNING\033[0m: error exporting current person to tursodb: {e}")
        
        if parsedorders.saveextra:
            try:
                values = {
                    
                }
        
                with self.engine.begin() as conn:
                    conn.execute(ppl_table.insert().values(**values))

            except Exception as e:
                if self.parsedorders.printbasic or self.parsedorders.printextra or self.parsedorders.printcount:
                    print(f"\033[1;31mWARNING\033[0m: error exporting current person to tursodb: {e}")

    def save_urls(self, filename="rollingurls.csv"):
        with open(filename, mode='w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            while not self.qdppl.empty():
                write_this = self.qdppl.get()
                writer.writerow([write_this,])


class Flags():

    def __init__(self, orders):
        self.orders = orders
        pieces = self.parse_user_input()
        self.url = pieces['url']
        self.rawflags = pieces['flags']
        self.scrape_limit = pieces['scrape_limit']
        self.printcount = True
        self.printbasic = False
        self.printextra = False
        self.savebasic = True
        self.saveextra = True  
        self.csvout = False
        self.tursoout = False
        self.savethisscrape = True
        self.uselastscrape = False
        self.printhelp = False
        self.setupdb = False
        self.flags = self.whichflags()
    
    def parse_user_input(self):
        tokens = self.orders.strip().split()

        #   re to get url
        url_pattern = re.compile(r"https?://(www\.)?linkedin\.com/\S+")

        url = None
        flags = set()
        limit_flag = None

        for token in tokens:
            #   get url
            if url_pattern.match(token):
                url = token
            #   get flags
            elif re.match(r"^-{1,2}[a-zA-Z]+$", token):
               flags.add(token)
            elif re.match(r"^-\d+$", token):  # e.g., -100
                limit_flag = abs(int(token))
           
        return {
            "url": url,
            "flags": flags,
            "scrape_limit": limit_flag
        }

    def whichflags(self):   
        if self.rawflags == None:
            return

        valid_flags = {'-h', '--help', '-q', '--quiet', '-b', '-e', '-B', '-E', '--csv', '-c', '-X', '-u', '-t'}
        unknown_flags = {
            flag for flag in self.rawflags
            if flag not in valid_flags and not re.match(r"^-\d+$", flag)
            }

        if '-h' in self.rawflags:
            self.printhelp = True
            return
        if '--help' in self.rawflags:
            self.printhelp = True
            return
        if '-q' in self.rawflags:
            self.printbasic = self.printextra = self.printcount = False
        if '--quiet' in self.rawflags:
            self.printbasic = self.printextra = self.printcount = False
        if '-s' in self.rawflags:
            self.setupdb = True
        if '--setup' in self.rawflags:
            self.setupdb = True
        if '-b' in self.rawflags:
            self.printbasic = True
        if '-e' in self.rawflags:
            self.printextra = True
        if '-B' in self.rawflags:
            self.savebasic = False
        if '-E' in self.rawflags:
            self.saveextra = False
        if '--csv' in self.rawflags:
            self.csvout = True
        if '-c' in self.rawflags:
            self.csvout = True
        if '-X' in self.rawflags:
            self.savethisscrape = False
        if '-u' in self.rawflags:
            self.uselastscrape = True
        if '-t' in self.rawflags: 
            self.tursoout = True
        
        if unknown_flags:
            print("\nignoring unrecognized flags:", ", ".join(unknown_flags), " beginning scrape!")
        
        
class Help():   
    
    def __init__(self):
        pass
    
    def helppage(self): 
        clear()
        #   \033[1;36m      cyan
        #   \033[0m         reset
        #   \033[1;31m      red
        print("""
    \033[1;36mLooped\033[1;31min\033[0m! [help page]
        

        [\033[1;36musage\033[0m]

        --help          print this message
        -h              print this message

        --quiet         do \033[1;31mNOT\033[0m print anything
        -q              do \033[1;31mNOT\033[0m print anything

        -B              do \033[1;31mNOT\033[0m save (\033[1;36mB\033[0m)ASIC data (in csv and/or turso)
        -E              do \033[1;31mNOT\033[0m save (\033[1;36mE\033[0m)XTRA data (in csv and/or turso)

        -b              DO print (\033[1;36mb\033[0m)ASIC data
        -e              DO print (\033[1;36me\033[0m)XTRA data

        --csv           DO export data to csv file
        -c              DO export data to csv file

        -t              DO export data to (\033[1;36mt\033[0m)urso db (requires .env setup)

        -X              e(\033[1;36mX\033[0m)clude current session urls (\033[1;31mwon't be saved\033[0m)
        -u              (\033[1;36mu\033[0m)se last saved session url list

        -s              (s)etup .env file (required for turso db)
        --setup         (s)etup .env file (required for turso db)


        [\033[1;36mbasic\033[0m vs \033[1;36mextra\033[0m]

        b is for BASIC data:

            url, title, uploader, views, duration, 
            upload date, likes/dislikes, keywords

        e is for EXTRA data:

            comments, description, hashtags, 
            heatmap, related urls


        [\033[1;36metc tips\033[0m]
        
        by default: 

            everything is saved, 
            only person tally is printed, terminal is kept clean for swag points!
            csv is \033[1;31mNOT\033[0m stored,
            session urls are preserved!

            quiet flags disable everything including person tally!
            if you're bored, print while you scrape!
            remember, BEbeq for flags!
            print is lowercase, save is uppercase, order does not matter
        """)

        choice = None
        choice = input(f"\n        press enter to start, type 'QUIT' to exit: ")

        if choice.strip().upper() == 'QUIT':
            exit(0)
        else:
            clear()
            print_art()
            main()
    
    def noinput(self):
        clear()
        print("""
    \033[1;31mWARNING\033[0m: no url given! did you mean -u? (use last session's urls)
        """)

        choice = None
        choice = input(f"\n        press enter to start, type 'QUIT' to exit: ")

        if choice.strip().upper() == 'QUIT':
            exit(0)
        else:
            clear()
            print_art()
            main()

    def nobothinputs(self):
        clear()
        print("""
    \033[1;31mWARNING\033[0m: previous session url list empty! verify the file or enter a new url
        """)

        choice = None
        choice = input(f"\n        press enter to start, type 'QUIT' to exit: ")

        if choice.strip().upper() == 'QUIT':
            exit(0)
        else:
            clear()
            print_art()
            main()

    def emptylistgiven(self):
        clear()
        print("""
    \033[1;31mWARNING\033[0m: url list empty! omit -u or verify rollingurls.csv is populated and in the correct place
        """)

        choice = None
        choice = input(f"\n        press enter to start, type 'QUIT' to exit: ")

        if choice.strip().upper() == 'QUIT':
            exit(0)
        else:
            clear()
            print_art()
            main()

    def twoinputs(self):
        clear()
        print("""
    \033[1;31mWARNING\033[0m: you cannot start a new scrape and use last input list! use either -u or provide a url    
        """)

        choice = None
        choice = input(f"\n        press enter to start, type 'QUIT' to exit: ")

        if choice.strip().upper() == 'QUIT':
            exit(0)
        else:
            clear()
            print_art()
            main()

    def envsetup(self):
        clear()
        print("""
    \033[1;31mWARNING\033[0m: .env incomplete!
        """)

        choice = None
        choice = input(f"\n        press enter to start, type 'SETUP' for .env setup, or type 'QUIT' to exit: ")

        if choice.strip().upper() == 'QUIT':
            exit(0)
        if choice.strip().upper() == 'SETUP':
            clear()
            
            db_url = input("enter your turso db url (to be stored locally, enter to skip): ").strip()
            clear()
            
            auth_token = input("enter your turso auth token (to be stored locally, enter to skip): ").strip()
            clear()
            linkedin_email = input("enter your linkedin email:")
            clear()
            linkedin_password = input("enter your linkedin password:")
            clear()
            print("""
        \033[1;31mWARNING\033[0m: 
        """)

            choice = None
            choice = input(f"\n        press enter to attempt auto login, or type 'QUIT' to exit(login credentials will \033[1;31mnot\033[0m be saved): ")

            if choice.strip().upper() == 'QUIT':
                exit(0)

            else:
                with open(".env", "w") as f:
                    f.write(f"TURSO_DB_URL={db_url}\n")
                    f.write(f"TURSO_AUTH_TOKEN={auth_token}\n")
                    f.write(f"LINKEDIN_EMAIL={linkedin_email}\n")
                    f.write(f"LINKEDIN_PASSWORD={linkedin_password}")
                    self.linkedin_login(driver, linkedin_email, linkedin_password)
        else:
            clear()
            print_art()
            main()

    def linkedin_login(self, driver, email, password):
        global parsedorders
        driver.get("https://www.linkedin.com/login")
        time.sleep(5)
        driver.find_element(By.ID, "username").send_keys(email)
        driver.find_element(By.ID, "password").send_keys(password)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(5)
        if is_logged_in(driver):
            checklist()
        else:
            self.login_failed()
        
    def login_failed(self):
        clear()
        print("""
    \033[1;31mWARNING\033[0m: login failed or captcha present, please attempt manual login or exit for .env check
        """)

        choice = None
        choice = input(f"\n        press enter to start, type 'LOGIN' for manual login, or type 'QUIT' to exit: ")

        if choice.strip().upper() == 'QUIT':
            exit(0)
        if choice.strip().upper() == 'LOGIN':
            driver.get("https://www.linkedin.com/login")
            input("\n   check your desktop for login prompt, and press enter here when completed...")

            if not is_logged_in(driver):
                self.login_failed()
        else:
            clear()
            print_art()
            main()


def main():
    global engine
    engine = None

    global driver
    
    chromedriver_path = shutil.which("chromedriver")

    options = Options()
    options.add_experimental_option("detach", True)
    
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--start-maximized")
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})


    #   GONNA HAVE TO MAKE SURE THIS IS A PER OS THING, FIX THIS
    options.binary_location = "/usr/bin/chromium"

   

    global driver

    service = Service(executable_path = chromedriver_path)

    driver = webdriver.Chrome(service = service, options=options)
    #   driver = webdriver.Chrome(service=Service(), options=options)

    if not Path(".env").exists():
        print(f"welcome! make sure you're logged in, then enter url and flags to get started: (-h or --help for info and -s or --setup for .env setup(\033[1;36mrecommended\033[0m))")
    else:
        print(f"welcome! make sure you're logged in, then enter url and flags to get started: (-h or --help for info)")
    orders = input("")
    global parsedorders
    parsedorders = Flags(orders)
    clear()
    #   print("DEBUG checklist url:", parsedorders.url)
    load_dotenv()

    EMAIL = os.getenv("LINKEDIN_EMAIL")
    PASSWORD = os.getenv("LINKEDIN_PASSWORD")
    
    if not EMAIL or not PASSWORD:
        Help().envsetup()

    if not is_logged_in(driver):
        Help().linkedin_login(driver, EMAIL, PASSWORD)

    checklist()

def checklist():
    global parsedorders
    global engine
    #   print("DEBUG checklist url:", parsedorders.url)
    try:
        cookies = pickle.load(open("linkedin_cookies.pkl", "rb"))
        for cookie in cookies:
            driver.add_cookie(cookie)
    except:
        print("could not open cookies, {e}, scraping anyway")

    driver.get("https://www.linkedin.com")  # Load a page to set domain


    driver.get("https://www.linkedin.com/feed/")
    
    url = parsedorders.url
    
    if parsedorders.printhelp:
        Help().helppage()

    if parsedorders.setupdb:
        Help().envsetup()

    TURSO_URL = os.getenv('TURSO_DB_URL')
    TURSO_TOKEN = os.getenv('TURSO_AUTH_TOKEN')

    if parsedorders.tursoout and not TURSO_URL and not TURSO_TOKEN:
        Help().envsetup()

    if parsedorders.tursoout:
        load_dotenv()
        engine = create_engine(
            f"{os.getenv('TURSO_DB_URL')}?authToken={os.getenv('TURSO_AUTH_TOKEN')}",
            connect_args={"uri": True}
            )
        
        metadata = MetaData()
    #   todo on turso test/upload with ALL scrapers
        ppl_table = Table(
            "people", metadata,
            Column("person_number", Integer),
            Column("url", Text),
            Column("startheat", Float),
            Column("endheat", Float),
            Column("peakheat", Float),
            Column("related_videos", Text)
            )
        metadata.create_all(engine)

    if not parsedorders.url and parsedorders.uselastscrape and not Path("rollingurls.csv").exists():
        Help().nobothinputs()

    if parsedorders.csvout:
        with open("output.csv", 'w', encoding='utf-8') as f:
            pass

    if not parsedorders.url and not parsedorders.uselastscrape:
        pass#   Help().noinput()

    if parsedorders.url and parsedorders.uselastscrape:
        Help().twoinputs()
    
    if parsedorders.scrape_limit == None:
        parsedorders.scrape_limit = 3

    Spider(url, parsedorders, engine)    
    
if __name__ == "__main__":  
    clear()
    print_art()
    main()

    