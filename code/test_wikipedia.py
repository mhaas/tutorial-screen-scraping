#!/usr/bin/python2
# -*- coding utf-8 -*-

import unittest
from wikipedia import Wikipedia


class WikipediaTest(unittest.TestCase):

  def setUp(self):
    self.term = 'scottish fold'
    self.fromDate = "01.01.1980"
    self.toDate = "01.01.2020"
    self.res = { "Wikipedia" : 25}
  

  def testFAZ(self):
    self._check("Wikipedia")

  def _check(self, source):
    o = Wikipedia()
    expected = self.res[source]
    count = 0
    iterator = o.crawl(self.term, self.fromDate, self.toDate)
    for mapping in iterator:
      # for now, only count cumulative results
      count += reduce(lambda x,y: x + len(y), mapping.values(), 0)
    self.assertEqual(count, expected, msg="source was %s, count %s, expected %s" % (source,count,expected))
   

if __name__ == '__main__':
  unittest.main() 
