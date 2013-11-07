#!/usr/bin/env python
# -*- coding: utf-8 -*-


import logging

import crockford as crock32
from google.appengine.api import files
from google.appengine.ext import blobstore
from google.appengine.ext import ndb

import acl
from . import revisions
from tools import common


__all__ = [
    'Error',
    'BaseModel',
    'MixyModel',
    'MixyExpando',
]


class Error(Exception):
  """Base error for this module."""
  pass


class BaseModel(object):
  """Base object mixin for base Model classes."""
  acl = acl.ACL(
      owner=acl.Permission(create=True, read=True, write=True, execute=True),
      group=acl.Permission(create=True, read=True, write=False, execute=False),
      world=acl.Permission(create=False, read=False, write=False, execute=False)
  )
  groups = []

  # Note(eric): This contains a list of fields that should be used as tags.
  _tag_attrs = ()

  @property
  def url_title(self):
    """Slugified title for use in URLs."""
    return common.slugify(self.title)

  @property
  def key_str(self):
    """String version of the instance key."""
    return self.key.urlsafe()

  @classmethod
  def CreateKey(cls, **kwargs):
    """Create a key for a new instance."""
    # Note(eric): Will kwargs cause breakage? Intended for parent support.
    future_ids = cls.allocate_ids_async(size=1)
    int_id, last_id = future_ids.get_result()
    str_id = crock32.urlencode(int_id)
    logging.debug('Allocate %s: %s to %s as %s', cls, int_id, last_id, str_id)
    return ndb.Key(cls, str_id, **kwargs)

  def make_tags(self):
    """Populate tags property with values from other fields, then clean up."""
    # Build list of tags from property names.
    tags = [getattr(self, x) for x in self._tag_attrs]
    # Slugify tags.
    tags = map(common.slugify, tags)
    # Remove dupes.
    tags = list(set(tags))
    # Return, if anything is left.
    return tags or None


class MixyModel(ndb.Model, BaseModel):
  """A base datastore model for all others to inherit from. Adds nice features
  and properties that all others will need."""
  id = ndb.ComputedProperty(lambda self: self.key.id())
  title = ndb.StringProperty(default='', indexed=False)
  tags = ndb.ComputedProperty(lambda self: self.make_tags())
  created_by = ndb.StringProperty()
  created = ndb.DateTimeProperty(auto_now_add=True)
  modified = ndb.DateTimeProperty(auto_now=True)
  disabled = ndb.BooleanProperty(default=False)
  store_revisions = ndb.BooleanProperty(default=False)
  revision = ndb.IntegerProperty(default=0)  # First rev will be 1, see pre-put.

  def _pre_put_hook(self):
    """Tasks to run before saving."""
    if self.store_revisions:
      self.revision += 1  # Increment revision number.
      logging.debug(u'%s revsion is now %d', self.key, self.revision)
    # TODO(eric): If disabled=True raise an exception and stop the put.

  def _post_put_hook(self, future):
    """Tasks to run after saving."""
    if self.store_revisions:
      logging.debug(u'Making call to save revision of %s', self.key)
      revisions.Revision.Save(future)

  def __copy__(self):
    """Copy method, calls to_dict."""
    obj_dict = self.to_dict(
        exclude=('id', 'created', 'modified', 'created_by', 'tags', 'revision'))
    return self.__class__(**obj_dict)

  def to_json(self, **kwargs):
    return common.ndb_json_dumps(self, **kwargs)

  @ndb.synctasklet
  def disable(self):
    """Set disabled=True."""
    self.disabled = True
    status = yield self.put_async()
    raise ndb.Return(status)

  @ndb.synctasklet
  def enable(self):
    """Set disabled=False."""
    self.disabled = False
    status = yield self.put_async()
    raise ndb.Return(status)


class MixyExpando(ndb.Expando, BaseModel):
  """Base expando class. Same as Model, but Expando!"""
  id = ndb.ComputedProperty(lambda self: self.key.id())
  title = ndb.StringProperty(default='', indexed=False)
  tags = ndb.ComputedProperty(lambda self: self.make_tags())
  created_by = ndb.StringProperty()
  created = ndb.DateTimeProperty(auto_now_add=True)
  modified = ndb.DateTimeProperty(auto_now=True)
  disabled = ndb.BooleanProperty(default=False)
  store_revisions = ndb.BooleanProperty(default=False)
  revision = ndb.IntegerProperty(default=0)  # First rev will be 1, see pre-put.

  def _pre_put_hook(self):
    """Tasks to run before saving."""
    if self.store_revisions:
      self.revision += 1  # Increment revision number.
      logging.debug(u'%s revsion is now %d', self.key, self.revision)
    # TODO(eric): If disabled=True raise an exception and stop the put.

  def _post_put_hook(self, future):
    """Tasks to run after saving."""
    if self.store_revisions:
      logging.debug(u'Making call to save revision of %s', self.key)
      revisions.Revision.Save(future)

  def __copy__(self):
    """Copy method, calls to_dict."""
    obj_dict = self.to_dict(
        exclude=('id', 'created', 'modified', 'created_by', 'tags', 'revision'))
    return self.__class__(**obj_dict)

  def to_json(self, **kwargs):
    return common.ndb_json_dumps(self, **kwargs)

  @ndb.synctasklet
  def disable(self):
    """Set disabled=True."""
    self.disabled = True
    status = yield self.put_async()
    raise ndb.Return(status)

  @ndb.synctasklet
  def enable(self):
    """Set disabled=False."""
    self.disabled = False
    status = yield self.put_async()
    raise ndb.Return(status)
