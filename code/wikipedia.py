#!/usr/bin/python2
# -*- coding: utf-8 -*-

from common import Article
import re
import urllib
from bs4 import BeautifulSoup
from leechi import Leechi
import logging
from crawler import Crawler
import datetime

logger = logging.getLogger(__name__)

"""
Crawls Wikipedia article archive.
"""
class Wikipedia(Crawler):

  def __init__(self):
    logging.basicConfig(level=logging.DEBUG, filename="%s.log" % __name__)
    self.base = "http://de.wikipedia.org/w/index.php?"
    self.l = Leechi()

  @staticmethod
  def getResultsPerPage():
    return 20

  @staticmethod
  def canFilterByDate():
    return False

  """
  Retrieves article meta data from article archive for a given search term and a given
  time span. The offset is used to navigate the paginated search results list.
  You probably want to put quotes around the search term for multi-word terms.
  
  The ID of the Article instances provided by this method are not provided
  by the data source. Instead, they are computed from hopefully unique
  (on a per-article basis) features.
 
  @param term {String} search term
  @param fromDate {String} Start date: dd.mm.yyyy
  @param toDate {String} End date: dd.mm.yyyy
  @param offset {Integer} For pagination
  """
  def fetch(self, term, fromDate, toDate, offset):
    res = []
    soup = self.getResultSoupForSearchTerm(term, fromDate, toDate, offset)
    ul = soup.find("ul", class_="mw-search-results")
    for li in ul.find_all("li"):
      # div class='mw-search-result-heading'
      heading = li.find('div', class_="mw-search-result-heading")
      url = "http://de.wikipedia.org" + heading.a["href"]
      title = "".join(heading.a.strings)
      articleID = title
      # TODO: does this get all strings?
      desc = "".join(li.find('div', class_="searchresult").strings)
      data = li.find('div', class_="mw-search-result-data").string
      dateRE = re.compile(ur"(\d{1,2})\. (\w{3})\.? (\d{4})", re.UNICODE)
      dateMatch = dateRE.search(data)
      # hardcode month to January because I can't be bothered to
      # make lookup table or proper parsing
      day = dateMatch.group(1)
      if len(day) == 1:
        day = "0" + day
      year = dateMatch.group(3)
      date = day + "." + "01" + "."  + year
      a = Article(articleID, date, title, "Unknown", "-1", "-1", desc)
      res.append(a)
    return res 

  """
  Gets BeautifulSoup instance for search term at given offset.
  You probably want to enclose the search term in double quotes.

  @param term Search Term
  @param fromDate {String} dd.mm.yyyy
  @param toDate {String} dd.mm.yyyy
  @param offset {Integer} For pagination
  """
  def getResultSoupForSearchTerm(self, term, fromDate, toDate, offset):
    if type(term) == unicode:
      term = term.encode("utf-8")
    params = {  "offset" : self.getResultsPerPage() * offset,
                "limit" : self.getResultsPerPage(),
                "title" : "Spezial:Suche",
                "fulltext" : "Search",
                "search" : urllib.quote_plus(term),
                "profile": "Default" }

    if offset == 0:
        del params["offset"]
        del params["limit"]
    url = self.base +  urllib.urlencode(params)
    logger.info("Constructed URL: %s", url)
    f = self.l.obtainHandleDelayed(url, params=None)
    soup = BeautifulSoup(f, "lxml" )
    return soup

if __name__ == "__main__":
  t = Wikipedia()
  t.main()
