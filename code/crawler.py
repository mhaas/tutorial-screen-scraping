#!/usr/bin/python2
# -*- coding: utf-8 -*-




from common import Article
import re
# to urlencode the parameters
import urllib
import BeautifulSoup
from leechi import Leechi
import logging
import datetime
import itertools

# logger is initialized in subclasses.
logger = logging.getLogger(__name__)

DATE_PATTERN = "%d.%m.%Y"

"""
Base class for article archive crawlers.
"""
class Crawler(object):

  def __init__(self):
    self.base = ""
    self.l = Leechi()
    raise NotImplementedError()

  """
  Remove article objects falling outside given date range.
  """
  @staticmethod
  def _filterByDate(articles, fromDate, toDate):
    pattern = DATE_PATTERN
    fromDateO = datetime.datetime.strptime(fromDate, pattern)
    toDateO = datetime.datetime.strptime(toDate, pattern)
    def f(x):
      articleDate = datetime.datetime.strptime(x.date, pattern)
      return articleDate >= fromDateO and articleDate <= toDateO
    articles = filter(f, articles)
    return articles

  """
  Whether a data source can return articles filtered by arbitrary date ranges.
  Most sources can do this.
  """
  @staticmethod
  def canFilterByDate():
    return True
  
  """
  Returns how many search results the data source presents per page.
  This is useful to determine when we're done crawling,
  e.g. if we get less than the specified amount per page.
  """
  @staticmethod
  def getResultsPerPage():
    return 10

  """
  Returns whether the data source only returns a limited number of
  results per query. If True, we need to fire multiple queries
  for a given time range to retrieve all results.
  """
  @staticmethod
  def isResultSetLimited():
    return False
 
  """
  Some scripts return articles for multiple sources.
  In this case, this method returns a set with source names.
  """
  @staticmethod
  def isMultiSource():
    return False
 
  """
  Retrieves article meta data from article archive for a given search term and a given
  time span. The offset is used to navigate the paginated search results list.
  You probably want to put quotes around the search term for multi-word terms.
  
  @param term {String} search term
  @param fromDate {String} Start date: dd.mm.yyyy
  @param toDate {String} End date: dd.mm.yyyy
  @param offset {Integer} For pagination
  """
  def fetch(self, term, fromDate, toDate, offset):
    raise NotImplementedError


  """
  Gets BeautifulSoup instance for search term at given offset.
  You probably want to enclose the search term in double quotes.

  @param term Search Term
  @param fromDate {String} dd.mm.yyyy
  @param toDate {String} dd.mm.yyyy
  @param offset {Integer} For pagination
  """
  def getResultSoupForSearchTerm(self, term, fromDate, toDate, offset):
    raise NotImplementedError()

  """
  Generator for article dictionary.
  Returns lists of articles till search results are exhausted.
  If the data source has a limit on the number of results per
  query, we call the crawler multiple times with narrow
  time ranges.
  A single crawler may return data for multiple sources.
  In this case, this method returns a mapping from
  source name to article list.
  If the crawler supports only a single source,
  a mapping from the "Default" source to its
  article list will be returned.
  """
  def crawl(self, term, fromDate, toDate):
    self.previousResultSet = set()
    if not self.isResultSetLimited():
      return self._crawl(term, fromDate, toDate)
    else:
      pattern = DATE_PATTERN
      fromDateO = datetime.datetime.strptime(fromDate, pattern)
      toDateO = datetime.datetime.strptime(toDate, pattern)
      # 2 weeks
      step = datetime.timedelta(14,0,0)
      oneDay= datetime.timedelta(1,0,0)
      logger.debug("step is %s", step)
      iterators = []
      origToDateO = toDateO
      while fromDateO < origToDateO:
        toDateO = fromDateO + step
        # do not overshoot
        if toDateO > origToDateO:
          toDateO = origToDateO
        curFromDate = fromDateO.strftime(pattern)
        curToDate = toDateO.strftime(pattern)
        logger.debug("Constructed time span: %s - %s", curFromDate, curToDate)
        iterators.append(self._crawl(term, curFromDate, curToDate))
        # the time range for search requests is inclusive:
        # if we do not add oneDay, we would do requests like this:
        # 1.6.2012 - 8.06.2012
        # 8.6.2012 - 15.06.2012
        # Thus grabbing articles for 8.6.2012 twice.
        # TODO: we do duplicate checking (to check if we arrived at the end of the article list)
        # below in _crawl, but not there. It would be wise to add some
        # sanity checks here.
        fromDateO = toDateO + oneDay
      # will yield for every element in iterators until exhausted
      return itertools.chain.from_iterable(iterators)
        
  
  """
  Generator for article lists. Returns lists of articles till search results are exhausted.
  """
  def _crawl(self, term, fromDate, toDate):
    self.offset = 0
    # num of results per page
    while True:
      resultsAtOffset = self.fetch(term, fromDate, toDate, self.offset)
      # treat single-source crawlers similar to multi-source crawlers
      # to simplify code handling
      if not self.isMultiSource():
        resultsAtOffset = { "Default" : resultsAtOffset}
      # we can't do the filtering in the fetch method, as this might result in
      # returning less than resultsPerPage (or even 0) articles
      # for some offsets even when we're not done retrieving articles.
      # Filtering based on resultsPerPage is tricky anyways and we might just throw
      # it out altogether.

      # if we have absolutely, positively no new results, just return.
      if not self.hasNewResults(resultsAtOffset):
        break
      if not self.canFilterByDate():
        dateFiltered = {}
        for key,result in resultsAtOffset.iteritems():
          dateFiltered[key] = self._filterByDate(result, fromDate, toDate)
        yield dateFiltered
      else:
        yield resultsAtOffset
      # TODO: if additional checks like hasEnoughResults were desired, these would go here.
      self.offset += 1 
   
  # used to check if we got at least resultsPerPage results
  def hasEnoughResults(self, resultsAtOffset):
    resultsLength = 0
    for key in resultsAtOffset:
      resultsLength = len(resultsAtOffset[key])
    if resultsLength < self.getResultsPerPage():
      logger.info("Found %s results,  which is less than resultsPerPage (%s), at offset %s", resultsLength, self.getResultsPerPage(), self.offset)
      return False
    return True

  # returns true iff we have articles in this run unseen during the previous offset
  def hasNewResults(self, resultsAtOffset):
    ret = self._hasNewResults(resultsAtOffset, 1)
    if not ret:
      logger.info("hasNewResults: returning False at offset %s", self.offset)
    return ret
  
  # returns true iff we number of unseen results is equal or bigger than resultsPerPage
  def hasEnoughNewResults(self, resultsAtOffset):
    ret = self._hasNewResults(resultsAtOffset, self.getResultsPerPage())
    if not ret:
      logger.info("hasEnoughNewResults: returning False at offset %s", self.offset)
    return ret

  def _hasNewResults(self, resultsAtOffset, minResults):
    currentResultSet = set()
    for l in resultsAtOffset.itervalues():
      currentResultSet.update([a.id for a in l])
    ret = True
    if len(currentResultSet - self.previousResultSet) < minResults:
      ret = False
    # keep whole history of seen articles, not only last res
    #self.previousResultSet = currentResultSet
    self.previousResultSet.update(currentResultSet)
    return ret

  def main(self):
    import sys
    if len(sys.argv) < 5: 
      print "Example usage: python2 script.py 'katze' 01.01.2000 31.03.2012 katze"
      exit(1)
    term = sys.argv[1]
    term = term.decode("utf-8")
    fromDate = sys.argv[2]
    toDate = sys.argv[3]
    out = sys.argv[4]
    generator = self.crawl(term, fromDate, toDate)
    outFiles = {}
    for mapping in generator:
      for source,articleList in mapping.iteritems():
        fileName = out + "_" + source + ".csv"
        if not fileName in outFiles:
          outFiles[fileName] = open(fileName, "w")
          outFiles[fileName].write(Article.getCSVHeader())
        outFile = outFiles[fileName]
        for article in articleList:
          outFile.write(article.getCSVRow())
    for outFile in outFiles.values():
      outFile.close()



