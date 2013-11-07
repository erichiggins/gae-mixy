#!/usr/bin/env python
# -*- coding: utf-8 -*-


import logging

from google.appengine.ext import ndb


__all__ = [
    'Revision',
]


class Revision(ndb.Expando):
  """Stored copy of a revisioned Model, stored copy of latest version."""
  obj_key = ndb.KeyProperty()
  dict = ndb.PickleProperty()
  revision = ndb.IntegerProperty()
  created = ndb.DateTimeProperty(auto_now_add=True)
  modified = ndb.DateTimeProperty(auto_now=True, indexed=False)

  @classmethod
  def Save(cls, future):
    """Save a copy of the object instance dictionary as a new Revision."""
    obj_key = future.get_result()
    obj = obj_key.get()
    logging.info(u'Saving revision %d of %s', obj.revision, obj_key)
    obj_dict = obj.to_dict()
    rev = cls(obj_key=obj_key, revision=obj.revision, dict=obj_dict)
    # TODO(eric): Use put_async.
    return rev.put()
