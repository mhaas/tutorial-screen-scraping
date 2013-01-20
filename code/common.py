#!/usr/bin/python2
# -*- coding: utf-8 -*-

import csv
import cStringIO

# TODO: needs search term
"""
Represents article meta data as retrieved from search results.
"""
class Article(object):
  def __init__(self, id, date, title, department, wordCount, price, bait):
    self.id = id
    self.date = date
    # band-aid
    if title is None:
      title = "unknown"
    self.title = title
    self.department = department
    self.wordCount = wordCount
    self.price = price
    self.bait = bait

  def __repr__(self):
    return self.getCSVRow();

  def __hash__(self):
    return hash(self.id)

  def __cmp__(self, other):
    # TODO: type check?!
    return cmp(hash(self),hash(other))

  @staticmethod
  def getCSVHeader():
    res = cStringIO.StringIO()
    writer = csv.writer(res,dialect='excel')
    writer.writerow(["ID","Date","Title","Department","WordCount","Price","Bait"])
    return res.getvalue()

  def getCSVRow(self):
    res = cStringIO.StringIO()
    writer = csv.writer(res,dialect='excel')
    row = [self.id.encode("utf-8")]
    row.append(self.date.encode("utf-8"))
    row.append(self.title.encode("utf-8"))
    row.append(self.department.encode("utf-8"))
    row.append(self.wordCount.encode("utf-8"))
    row.append(self.price.encode("utf-8"))
    row.append(self.bait.encode("utf-8"))
    #timepattern = "%d.%m.%Y %H:%M"
    #row.append(self.timeStamp.strftime(timepattern))
    writer.writerow(row)
    return res.getvalue()

  @staticmethod
  def fromCSVRow(row):
    row = map(lambda x: x.decode("utf-8"), row)
    return Article(row[0], row[1], row[2], row[3], row[4], row[5], row[6])


