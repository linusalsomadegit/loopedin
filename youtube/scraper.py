import requests
import shutil
import yt_dlp
import queue
import json
import csv
import re
import os
from dotenv import load_dotenv
from pathlib import Path
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, Text
from sqlalchemy.orm import sessionmaker
from youtube_transcript_api import (
YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, VideoUnavailable)
from collections import Counter
from urllib.parse import urlparse, parse_qs, urljoin

import traceback
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
from bs4 import BeautifulSoup

import common.art as art;


#   for below, had to clone the repo and put it in 
#   /usr/lib/python3.13/site-packages/youtube_comment_downloader
#   making sure to extract only the folder with downloader.py, __main__.py, and __init__.py
#   imports the class YoutubeCommentDownloader in file downloader.py
from youtube_comment_downloader import YoutubeCommentDownloader


def clear():
            os.system('cls' if os.name == 'nt' else 'clear')


class Vidya:

    def __init__(self, url):
        #   make sure it checks url BEFORE EVERYTHING ELSE
        #   if self.url == None BREAK, or create a url checker      #   was gonna use v to copy 
        #                                                           #   but it doesnt work
        self.url = self.normalize_url(url)                          #   url
        self.video_id = self.get_video_id()                         #   video_id
        self.metadata = self.get_metadata()                         #   metadata
        self.transcript = self.get_transcript()                     #   transcript
        self.dislikes = self.get_dislike_count()                    #   dislikes
        self.comments = self.get_comments()                         #   comments
        #   probably good to implement error handling for below v
        self.description = self.get_description()                   #   description
        self.views = self.get_views()                               #   views
        self.likes = self.get_likes()                               #   likes
        self.title = self.get_title()                               #   title
        self.dateup = self.get_dateup()                             #   dateup
        self.duration = self.get_duration()                         #   duration
        self.related_videos = self.get_related_videos()             #   related_videos
        self.hashtags = self.get_hashtags()                         #   hashtags
        self.uploader = self.get_uploader()                         #   uploader
        self.music = self.get_music()                               #   probably don't touch the
        self.keywords = self.get_keywords()                         #   music for now
        #   easiest to group these into one method v
        #   also note for using real heatmap there's start and end times for each
        #   point of data so this is using start, just a note
        peaks = self.getpeaks()                                     
        self.startheat = peaks['start_peak']                        
        self.endheat = peaks['end_peak']
        self.peakheat = peaks['hottest_point']

        #   music is a little iffy and not super relevant but it works most of the time ^
        #   maybe use maybe not
        #   self.worked = self.diditreally()
        # ^ 0 is no, 1 is yes for ALL fields filled

    def normalize_url(self, url):
        parsed = urlparse(url)
        if "youtu.be" in parsed.netloc:
            video_id = parsed.path.strip("/")
            return f"https://www.youtube.com/watch?v={video_id}"
        match = re.search(r'(?:v=)?([A-Za-z0-9_-]{11})', url)
        if match:
            video_id = match.group(1)
            return f"https://www.youtube.com/watch?v={video_id}"
        return url
    
    def get_video_id(self):
        query = parse_qs(urlparse(self.url).query)
        return query["v"][0] if "v" in query else self.url.split("/")[-1]

    def get_metadata(self):
        ydl_opts = {
            'quiet': True,
            'extract_flat': False,
            'skip_download': True,
            #   'force_generic_extractor': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(self.url, download=False)
    
    def get_transcript(self):
        try:
            self.transcript = YouTubeTranscriptApi.get_transcript(video_id)
            return " ".join([entry["text"] for entry in self.transcript])
        except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable):
            return None
        except Exception as e:
            #   for debugging v
            #   print(f"[⚠️ Transcript Error] Could not fetch transcript for video {video_id}: {e}")
            return None

    def get_dislike_count(self):
        r = requests.get(f"https://returnyoutubedislikeapi.com/votes?videoId={self.video_id}")
        if r.status_code == 200:
            return r.json().get("dislikes", None)
        return None

    def get_comments(self):
        #   SEE LIMIT COMMENT BELOW IMPORT
        limit = 10
        downloader = YoutubeCommentDownloader()
        comments = []
        for comment in downloader.get_comments_from_url(f"https://www.youtube.com/watch?v={self.video_id}"):
            comments.append(comment['text'])
            if len(comments) >= limit:
                break
        return comments

    def get_description(self):
        return self.metadata.get("description", "")

    def get_views(self):
        return self.metadata.get("view_count")
        
    def get_likes(self):
        return self.metadata.get("like_count")

    def get_title(self):
        return self.metadata.get("title")

    def get_dateup(self):
        return self.metadata.get("upload_date")
        
    def get_duration(self):
        return self.metadata.get("duration")

    def get_related_videos(self):
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("user-agent=Mozilla/5.0")

        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

        try:
            driver.get(self.url)
            time.sleep(5)  # Let JS render related videos

            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")

            related_urls = set()

            for link in soup.find_all("a", href=True):
                href = link["href"]
                if "/watch?v=" in href:
                    if href.startswith("/watch?v="):
                        href = "https://www.youtube.com" + href
                    elif href.startswith("watch?v="):
                        href = "https://www.youtube.com/" + href
                    elif not href.startswith("http"):
                       #     print(f"[WARN] Skipping malformed href: {href}")
                        return

# Strip unnecessary params
                    clean_url = href.split("&")[0]
                    normalized = self.normalize_url(clean_url)
                    if normalized != self.url:
                        related_urls.add(normalized)

            #   print(f"[DEBUG] Extracted {len(related_urls)} related URLs from HTML")
            return list(related_urls)

        except Exception as e:
            import traceback
            print(f"selenium failed to get related videos: {e}")
            traceback.print_exc()
            return []

        finally:
            driver.quit()

    def get_hashtags(self):
        def removetags(text):
            return re.findall(r"#\w+", text)
        
        titletags = removetags(self.title or "")
        descriptiontags = removetags(self.description or "")
        commenttags = removetags(" ".join(self.comments) if self.comments else "")

        return list(set(titletags + descriptiontags + commenttags))

    def get_uploader(self):
        return self.metadata.get("uploader")

    def get_music(self):
        music_lines = []

        if 'metadata' in self.metadata:
            for item in self.metadata['metadata']:
                label = item.get("label", "").lower()
                value = item.get("value", "")
                if "music" in label or "song" in label:
                    music_lines.append(f"{label}: {value}")

        # Fallback to regex search in description
        if not music_lines:
            pattern = re.compile(r"(?i)(music|song|track|licensed|provided by).*")
            music_lines = [line.strip() for line in self.description.split("\n") if pattern.search(line)]

        return music_lines or None

    def getpeaks(self):
        heatmap = self.getrealmap()
        if heatmap:
            peaks = self.normalmap(heatmap)
        else:
            peaks = self.guessmap()

        if peaks:
            return peaks
        else:
            return None

    def getrealmap(self):
        if 'heatmap' in self.metadata:
            return self.metadata['heatmap']
        chapters = self.metadata.get('chapters', [])
        for chapter in chapters:
            if 'heatmap' in chapter:
                return chapter['heatmap']
        return None

    def normalmap(self, heatmap):
        intensities = [point['value'] for point in heatmap]
        avg = sum(intensities) / len(intensities)
        threshold = avg * 1.2

        #   ALSO CAN DYNAMICALLY TWEAK THIS ^ BUT AS TESTED WORKS FINE DONT TOUCH IT
        hot_spots = [point for point in heatmap if point['value'] >= threshold]
        if not hot_spots:
            return {
                "start_peak": None,
                "end_peak": None,
                "hottest_point": max(heatmap, key=lambda x: x['value'])['start_time']
            }

        return {
            "start_peak": hot_spots[0]['start_time'],
            "end_peak": hot_spots[-1]['start_time'],
            "hottest_point": max(hot_spots, key=lambda x: x['value'])['start_time']
        }
        
    def guessmap(self):
        heatmap = self.getguessmap()
        if not heatmap:
            return None
            
        scores = [h["score"] for h in heatmap]
        avg = sum(scores) / len(scores) if scores else 0
        threshold = avg * 1.2

        hot_chunks = [h for h in heatmap if h["score"] >= threshold]

        if not hot_chunks:
            hottest = max(heatmap, key=lambda x: x["score"])
            return {
                "start_peak": None,
                "end_peak": None,
                "hottest_point": (hottest["start"] + hottest["end"]) // 2
            }

        return {
            "start_peak": hot_chunks[0]["start"],
            "end_peak": hot_chunks[-1]["end"],
            "hottest_point": max(hot_chunks, key=lambda x: x["score"])["start"]
        }

    def extract_timestamp_comments(self):
        if not self.comments:
            return []
        pattern = re.compile(r"\b(?:\d+:)?\d{1,2}:\d{2}\b")
        seconds_list = []

        for comment in self.comments:
            for match in pattern.finditer(comment):
                full_match = match.group(0)
                parts = list(map(int, full_match.strip(":").split(":")))
                try:
                    if len(parts) == 3:
                        seconds = parts[0]*3600 + parts[1]*60 + parts[2]
                    elif len(parts) == 2:
                     seconds = parts[0]*60 + parts[1]
                    else:
                        seconds = parts[0]
                    seconds_list.append(seconds)
                except Exception:
                   continue
        return seconds_list

    def chunk_video(self, chunksize):
        if not self.duration:
            return []
        return [(i, min(i + chunksize, self.duration)) 
        for i in range(0, self.duration, chunksize)]

    def getguessmap(self):
        chunksize = 30
        #   arbitrary for now may change later ^
            
        chunks = self.chunk_video(chunksize)
        transcript_counts = [0] * len(chunks)
        comment_counts = [0] * len(chunks)

        #   Process transcript
        if self.transcript:
            for entry in self.transcript:
                time = int(entry['start'])
                index = time // chunksize
                if index < len(transcript_counts):
                    transcript_counts[index] += len(entry['text'].split())

        #   Process comment timestamps
        timestamps = self.extract_timestamp_comments()
        for t in timestamps:
            index = t // chunksize
            if index < len(comment_counts):
                comment_counts[index] += 1

        heatmap = []
        for i, (start, end) in enumerate(chunks):
            score = transcript_counts[i] + comment_counts[i]
            heatmap.append({"start": start, "end": end, "score": score})
        return heatmap

    def get_keywords(self):
        all_texts = []

        if self.title:
            all_texts.append(self.title)
        if self.description:
            all_texts.append(self.description)
        if self.transcript:
            all_texts.append(self.transcript)
        if self.uploader:
            all_texts.append(self.uploader)
        if self.comments:
            all_texts.append(" ".join(self.comments))

        #   Boosted hot transcript
        hotspot_text = ""
        if self.transcript and self.peakheat:
            try:
                hot_center = int(self.peakheat)
                window_size = self.duration / 10    #   yeah maybe change that
                hotspot_texts = []
                for entry in self.transcript:
                    try:
                        if abs(int(entry['start']) - hot_center) <= window_size:
                            hotspot_texts.append(entry['text'])
                    except:
                        continue
                hotspot_text = " ".join(hotspot_texts * 3)  # Weighted
                all_texts.append(hotspot_text)
            except:
                pass

        #   everything here and then cleaned
        full_text = " ".join(all_texts)
        words = Vidya.clean_text(full_text)
        freq = Counter(words)
                                                    #   v probably gonna wanna change that 
                                                    #   dynamically to see if something really
                                                    #   catches on or isnt worth our time,
                                                    #   see window size as well for length of
                                                    #   video
        return [word for word, _ in freq.most_common(50)]

    @staticmethod
    def clean_text(text):
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        stopwords = set([
            "the", "and", "for", "with", "you", "this", "that", "have", "are", "from", "they",
            "was", "your", "but", "not", "all", "can", "just", "like", "get", "one", "out",
            "been", "what", "when", "where", "will", "would", "should", "could", "about", "more",
            "some", "into", "over", "them", "those", "then", "than", "his", "her", "she", "him",
            "our", "their", "how", "why", "who", "which", "were", "there", "because", "also", "did"
        ])
        return [word for word in words if word not in stopwords]    #   can also append
                                                                    #   other words we find to
                                                                    #   be irrelevant

    def diditreally(self):
        #   if ANYTHING is empty return 0
        fields = [
            self.url, self.video_id, self.metadata, self.transcript,
            self.dislikes, self.comments, self.description,
            self.views, self.likes, self.title, self.dateup,
            self.duration, self.music
        ]
        return 0 if any(f is None for f in fields) else 1

class Spider:

    #   think about implementing storage for qdvids urls so that they 
    #   can be used again if the program stops for any reason, config to 
    #   store this info somewhere and then a flag to pickup where left offrq

    def __init__(self, url, parsedorders, engine):
        #   clear()
        self.engine = engine
        self.qdvids = queue.Queue()
        self.parsedorders = parsedorders
        
        if url is not None:
            self.qdvids.put(url)
        self.tally = 0
        self.seen = set()
        self.stopat = parsedorders.scrape_limit 
        if self.tally == 0:
            self.loadlastqueue()
        if self.qdvids.empty() and self.parsedorders.uselastscrape:
            Help().emptylistgiven()
        self.recurse()
         
    def recurse(self):
        #   gonna export the data here somehow, probably in Out class, but 
        #   for now just print
        while not self.qdvids.empty() and self.tally < self.stopat:
            current_url = self.qdvids.get()
            if current_url in self.seen:
                continue
            self.seen.add(current_url)

            try:
                vid = Vidya(current_url)

                self.tally += 1

                Rambling(vid, self.tally, self.parsedorders, self.stopat, self.qdvids, self.engine, self.seen)

                for new_url in vid.related_videos: 
                    clean_url = Vidya(new_url).normalize_url(new_url)    #   logic here to determine next url < dynamic
                    if clean_url not in self.seen:                          #   and should be done with keywords in mind,  
                        self.qdvids.put(clean_url)                       #   how many comments/recs is dynamic based on 
            except Exception as e:                                      #   what is relevant and found, see todo doc
                #   if self.tally > 0:
                print(f"Error scraping {current_url}: {e}")
        
    def loadlastqueue(self, filename="rollingurls.csv"):
        if self.parsedorders.uselastscrape:                 # and self.qdvids == None:
            with open(filename, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("http"):
                        self.qdvids.put(line)

            with open(filename, 'w', encoding='utf-8') as f:
                pass
            return self.qdvids

    
class Rambling:
    
    def __init__(self, this_video, tally, parsedorders, stopat, qdvids, engine, seen):
        self.parsedorders = parsedorders
        self.stopat = stopat
        self.engine = engine
        self.vid1 = this_video
        self.tally = tally
        self.qdvids = qdvids
        self.seen = seen
            
        if self.parsedorders.printcount:
            clear()
            print(f"vid # in search: \033[1;36m{self.tally}\033[0m")

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
       
        print(f"\nurl: {self.vid1.url}")
        print(f"\ntitle: {self.vid1.title}")
        print(f"\nuploader: {self.vid1.uploader}")
        print(f"\nviews: {self.vid1.views}")
        print(f"\nduration: {self.vid1.duration}")
        print(f"\nupload date: {self.vid1.dateup}")
        print(f"\nlikes: {self.vid1.likes}")
        print(f"\ndislikes (not youtube's): {self.vid1.dislikes}")
        print(f"\nkey words: {self.vid1.keywords}")

    def printextra(self):

        print(f"\ncomments: {self.vid1.comments}")
        print(f"\ndescription: {self.vid1.description}")
        print(f"\nhashtags: {self.vid1.hashtags}")
        print(f"\nretention starts: {self.vid1.startheat}")
        print(f"\nretention ends: {self.vid1.endheat}")
        print(f"\nretention peaks: {self.vid1.peakheat}")
        print(f"\nrelated urls: {self.vid1.related_videos}")

    def export_csv(self, filename="output.csv"):

        with open(filename, mode='a', newline='', encoding='utf-8') as csvfile:
            #   writer.writerow(self.vid1.__dict__.values()) this is ludicrous it could
            #   be cool but we'll see, based on flags
            if self.vid1 is not None:
                writer = csv.writer(csvfile)
                if self.parsedorders.savebasic:
                    writer.writerow([
                        self.tally,
                        self.vid1.url,
                        self.vid1.title,
                        self.vid1.uploader,
                        self.vid1.views,
                        self.vid1.duration,
                        self.vid1.dateup,
                        self.vid1.likes,
                        self.vid1.dislikes,
                        self.vid1.keywords
                    ])
                    
                if self.parsedorders.saveextra:
                    writer.writerow([
                        self.vid1.comments,
                        self.vid1.description,
                        self.vid1.hashtags,
                        self.vid1.startheat,
                        self.vid1.endheat,
                        self.vid1.peakheat,
                        self.vid1.related_videos,
                    ])

                if self.tally == 0:
                    if self.parsedorders.savebasic:
                        basic = """video_number, url, title, uploader, views, duration, dateup, likes, dislikes, keywords, """
                        writer.writerow(basic)
                    if self.parsedorders.saveextra:
                        extra = """comments, description, hashtags, startheat, endheat, peakheat, related_videos, """

    def scrape_finished(self):
        #   clear()
        print(f"\n")
        print(f"scrape complete!")
        print(f"\n")
        print(f"thank you for using")
        art.print_art()
        if self.parsedorders.savethisscrape == True:
            self.save_urls()
        exit(0)
    
    def export_turso(self):
        if parsedorders.savebasic:
            try:
                values = {
                    'vid_number': self.tally + 1,
                    'url': self.vid1.url,
                    'title': self.vid1.title,
                    'uploader': self.vid1.uploader,
                    'views': self.vid1.views,
                    'duration': self.vid1.duration,
                    'dateup': self.vid1.dateup,
                    'likes': self.vid1.likes,
                    'dislikes': self.vid1.dislikes,
                    'keywords': ", ".join(self.vid1.keywords) if self.vid1.keywords else None,
                }
        
                with self.engine.begin() as conn:
                    conn.execute(video_table.insert().values(**values))
        
            except Exception as e:
                if self.parsedorders.printbasic or self.parsedorders.printextra or self.parsedorders.printcount:
                    print(f"\033[1;31mWARNING\033[0m: error exporting current vid to tursodb: {e}")
        
        if parsedorders.saveextra:
            try:
                values = {
                    'comments': "\n".join(self.vid1.comments) if self.vid1.comments else None,
                    'description': self.vid1.description,
                    'hashtags': ", ".join(self.vid1.hashtags) if self.vid1.hashtags else None,
                    'startheat': self.vid1.startheat,
                    'endheat': self.vid1.endheat,
                    'peakheat': self.vid1.peakheat,
                    'related_videos': ", ".join(self.vid1.related_videos) if self.vid1.related_videos else None
                }
        
                with self.engine.begin() as conn:
                    conn.execute(video_table.insert().values(**values))

            except Exception as e:
                if self.parsedorders.printbasic or self.parsedorders.printextra or self.parsedorders.printcount:
                    print(f"\033[1;31mWARNING\033[0m: error exporting current vid to tursodb: {e}")

    def save_urls(self, filename="rollingurls.csv"):
        with open(filename, mode='w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            for url in self.seen:
                writer.writerow([url])



class Flags():
    #   have numerical flag (-5) for scrape specificity, dynamic if blank
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
        url_pattern = re.compile(r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/\S+")

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
        
        
class Help():   #   print help here, then go back to entering info
    def __init__(self):
        pass
    
    def helppage(self): 
        #   don't forget to say where the persistent option will be
        clear()
        #   \033[1;36m      cyan
        #   \033[0m         reset
        #   \033[1;31m      red
        print("""
    \033[1;36mScrape\033[1;31mYou\033[0m! [help page]
        

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
            only video tally is printed, terminal is kept clean for swag points!
            csv is \033[1;31mNOT\033[0m stored,
            session urls are preserved!

            quiet flags disable everything including video tally!
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
            art.print_art()
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
            art.print_art()
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
            art.print_art()
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
            art.print_art()
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
            art.print_art()
            main()

    def envsetup(self):
        clear()
        print("""
    \033[1;31mWARNING\033[0m: .env does not exist! 
        """)

        choice = None
        choice = input(f"\n        press enter to start, type 'SETUP' for .env setup, or type 'QUIT' to exit: ")

        if choice.strip().upper() == 'QUIT':
            exit(0)
        if choice.strip().upper() == 'SETUP':
            clear()
            db_url = input("enter your turso db url (to be stored locally): ").strip()
            clear()
            auth_token = input("enter your turso auth token (to be stored locally): ").strip()

            with open(".env", "w") as f:
                f.write(f"TURSO_DB_URL={db_url}\n")
                f.write(f"TURSO_AUTH_TOKEN={auth_token}\n")
        else:
            clear()
            art.print_art()
            main()


def main():
    engine = None
    if not Path(".env").exists():
        print(f"welcome! enter url and flags to get started: (-h or --help for info and -s or --setup for .env setup(\033[1;36mrecommended\033[0m))")
    else:
        print(f"welcome! enter url and flags to get started: (-h or --help for info)")
    orders = input("")
    clear()
    parsedorders = Flags(orders)
    url = parsedorders.url
    
    if parsedorders.printhelp:
        Help().helppage()

    if parsedorders.setupdb:
        Help().envsetup()

    if parsedorders.tursoout and not Path(".env").exists():
        Help().envsetup()

    if parsedorders.tursoout:
        load_dotenv()
        engine = create_engine(
            f"{os.getenv('TURSO_DB_URL')}?authToken={os.getenv('TURSO_AUTH_TOKEN')}",
            connect_args={"uri": True}
            )
        
        metadata = MetaData()

        video_table = Table(
            "videos", metadata,
            Column("vid_number", Integer),
            Column("url", String),
            Column("title", String),
            Column("uploader", String),
            Column("views", Integer),
            Column("duration", Float),
            Column("dateup", String),
            Column("likes", Integer),
            Column("dislikes", Integer),
            Column("keywords", Text),
            Column("comments", Text),
            Column("description", Text),
            Column("hashtags", Text),
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
        Help().noinput()

    if parsedorders.url and parsedorders.uselastscrape:
        Help().twoinputs()
    
    if parsedorders.scrape_limit == None:
        parsedorders.scrape_limit = 3

    Spider(url, parsedorders, engine)
    
if __name__ == "__main__":  
    clear()
    art.print_art()
    main()
