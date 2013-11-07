#!/usr/bin/env python
# -*- coding: utf-8 -*-


import base64
import datetime
import json
import re
import time
import unidecode
import dateutil.parser
from google.appengine.ext import ndb


def slugify(value):
  """Slugify a string/unicode value, commonly for pretty URLs."""
  slug_char = '_'
  value = unidecode.unidecode(value).lower()
  slugified = re.sub(r'\W+', slug_char, value)
  return slugified.strip(slug_char)


class NdbEncoder(json.JSONEncoder):
  """Extend the JSON encoder to add support for NDB Models."""

  def default(self, obj):

    if hasattr(obj, 'to_dict'):
      obj_dict = obj.to_dict()
      # Encode binary strings (blobs) to base64.
      for k, v in obj_dict.iteritems():
        if isinstance(v, str):
          try:
            unicode(v)
          except UnicodeDecodeError:
            obj_dict[k] = base64.b64encode(v)
      return obj_dict

    elif isinstance(obj, ndb.query.Query):
      return list(obj)

    elif isinstance(obj, ndb.query.QueryIterator):
      return list(obj)

    elif isinstance(obj, ndb.model.Key):
      return obj.get()

    elif isinstance(obj, datetime.datetime):
      # Reformat the date slightly for better JS compatibility.
      # Offset-naive dates need 'Z' appended for JS.
      zone = '' if obj.tzinfo else 'Z'
      return obj.isoformat() + zone

    elif isinstance(obj, time.struct_time):
      return list(obj)

    elif isinstance(obj, complex):
      return [obj.real, obj.imag]

    return json.JSONEncoder.default(self, obj)


def ndb_json_dumps(ndb_model, **kwargs):
  """Custom json dumps using the custom encoder above."""
  return NdbEncoder(**kwargs).encode(ndb_model)


def ndb_json_dump(ndb_model, fp, **kwargs):
  """Custom json dump using the custom encoder above."""
  for chunk in NdbEncoder(**kwargs).iterencode(ndb_model):
    fp.write(chunk)


def ndb_json_loads(json_str, **kwargs):
  """Custom json loads function that converts datetime strings."""
  json_dict = json.loads(json_str, **kwargs)
  if isinstance(json_dict, list):
    return map(ndb_json_iteritems, json_dict)
  return ndb_json_iteritems(json_dict)


def ndb_json_iteritems(json_dict):
  """Loop over a json dict and try to convert strings to datetime."""
  for key, val in json_dict.iteritems():
    if isinstance(val, dict):
      ndb_json_iteritems(val)
    # Its a little hacky to check for specific chars, but avoids integers.
    elif isinstance(val, basestring) and 'T' in val:
      try:
        json_dict[key] = dateutil.parser.parse(val)
        # Check for UTC.
        if val.endswith(('+00:00', '-00:00', 'Z')):
          # Then remove tzinfo for gae, which is offset-naive.
          json_dict[key] = json_dict[key].replace(tzinfo=None)
      except ValueError:
        pass
  return json_dict
