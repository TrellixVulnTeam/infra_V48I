# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import re
import requests
import sqlite3
import time


def extract_json_data(rietveld_url):  # pragma: no cover
  url_components = re.split('(https?:\/\/)([\da-z\.-]+)', rietveld_url)
  json_data_url = '%s%s/api%s?messages=true' %(url_components[1],
                  url_components[2], url_components[3])
  response = requests.get(json_data_url)
  if (response.status_code == requests.codes.ok):
    return response.json()
  else:
    response.raise_for_status()


def contains_lgtm(json_data):
  for message in json_data['messages']:
    if message['approval']:
      return True
  return False


def contains_tbr(json_data):
  description = json_data['description']
  return any(
        not line.strip().startswith('>') and re.search(r'^TBR=.*', line)
        for line in description.splitlines())


def to_canonical_rietveld_url(rietveld_url):
  if 'chromiumcodereview.appspot.com' in rietveld_url:
    return rietveld_url.replace('chromiumcodereview.appspot.com',
                                'codereview.chromium.org') 
  if 'chromiumcodereview-hr.appspot.com' in rietveld_url:
    return rietveld_url.replace('chromiumcodereview-hr.appspot.com', 
                                'codereview.chromium.org')
  return rietveld_url


def add_rietveld_data_to_db(rietveld_url, file_name):  # pragma: no cover
  rietveld_url = to_canonical_rietveld_url(rietveld_url)
  write_data_to_db(rietveld_url, extract_json_data(rietveld_url), file_name)


def write_data_to_db(rietveld_url, json_data, file_name):
  con = sqlite3.connect(file_name)
  with con:
    cur = con.cursor()
    db_data = (json_data['issue'], contains_lgtm(json_data), 
               contains_tbr(json_data), time.time(), rietveld_url)
    cur.execute('INSERT OR REPLACE INTO rietveld VALUES (?, ?, ?, ?, ?)', 
                db_data)