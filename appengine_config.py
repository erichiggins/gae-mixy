#/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import sys


# Zipimport libraries.
# Eric's note: I've swapped these zips with new files created from
#   'python setup.py build'. when available.
THIRD_PARTY_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'third_party')
LIBS = (
    'arrow-0.4.1.zip',
    'babel-0.9.6.zip',
    'crockford-0.0.2-modified.zip',
    'dateutil-2.1.zip',
    'gdata-2.0.17.zip',
    'html5lib-0.95.zip',
    'httplib2-0.7.6.zip',
    'jinja2htmlcompress.zip',
    'markdown-2.2.0.zip',
    'oauth2-1.5.211.zip',
    'pytz-2012c-modified.zip',
    'simpleauth-0.1.3.zip',
    'six-1.4.1.zip',
    'unidecode-0.04.9.zip',
    'wtforms-1.0.5.zip',
)
for filename in LIBS:
  sys.path.insert(1, os.path.join(THIRD_PARTY_PATH, filename))


# AppStats configuration.
appstats_CALC_RPC_COSTS = True
appstats_MAX_STACK = 15


def webapp_add_wsgi_middleware(app):
  """Enables appstats middleware."""
  from google.appengine.ext.appstats import recording
  return recording.appstats_wsgi_middleware(app)
