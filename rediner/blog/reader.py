from pyquery import PyQuery as pq
from collections import deque
import requests

import argparse
import sys
import re


# https://stackoverflow.com/a/49146722/330558
emoji_pattern = re.compile("["
   u"\U0001F600-\U0001F64F"  # emoticons
   u"\U0001F300-\U0001F5FF"  # symbols & pictographs
   u"\U0001F680-\U0001F6FF"  # transport & map symbols
   u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
   u"\U00002702-\U000027B0"
   u"\U000024C2-\U0001F251"
   "]+", flags=re.UNICODE)
def remove_emoji(string):
   return emoji_pattern.sub(r'', string)


def get_document(url):
   r = requests.get(url)
   d = pq(remove_emoji(r.text))
   return d

def blog_entry_pages(*args,entries=['article[typeof]', '.header-hero-content a','.tableau-result a'],next=["header .article-navigation a[title='preceding entry']",'.wp-pagenavi a.page'],verbose=False,action=None):
   pages = deque()
   entry_urls = set()
   for arg in args:
      pages.append(arg)
      visited = set()
      while pages:
         url = pages.pop()
         if url in visited:
            continue
         visited.add(url)

         if verbose:
            print('Harvesting entry pages from '+url,file=sys.stderr)

         d = get_document(url)

         for pattern in entries:
            for e in d(pattern):
               entry_url = e.attrib.get('href')
               if entry_url is None:
                  entry_url = e.attrib.get('resource')
               if entry_url is None:
                  entry_url = e.attrib.get('src')
               if entry_url is not None:
                  final_url = requests.compat.urljoin(url,entry_url)
                  if final_url not in entry_urls:
                     entry_urls.add(final_url)
                     yield final_url, action(final_url,d) if action is not None else None

         for pattern in next:
            for e in d(pattern):
               next_url = e.attrib['href']
               if verbose:
                  print('adding: '+next_url,file=sys.stderr)
               pages.append(next_url)
