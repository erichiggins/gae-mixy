#!/usr/bin/env python
# -*- coding: utf-8 -*-


import logging
import json
import time

from google.appengine.api import search
from google.appengine.ext import ndb

import acl
from . import base


TODO_INDEX = search.Index(name='todo')


class ToDo(base.MixyModel):
  acl = acl.ACL(
      owner=acl.Permission(create=True, read=True, write=True, execute=True),
      group=acl.Permission(create=True, read=True, write=False, execute=True),
      world=acl.Permission(create=False, read=True, write=False, execute=False)
  )
  task = ndb.StringProperty()
  assignee = ndb.StringProperty()
  due = ndb.DateProperty()

  def _post_put_hook(self, future):
    TODO_INDEX.put(self._document)

  @classmethod
  def _post_delete_hook(cls, key, future):
    TODO_INDEX.delete(key.string_id())

  @property
  def _document(self):
    return search.Document(doc_id=self.id, fields=[
        search.TextField(name='task', value=self.task),
        search.TextField(name='assignee', value=self.assignee),
        search.DateField(name='due', value=self.due),
    ])
