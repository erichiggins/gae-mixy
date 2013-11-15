#!/usr/bin/env python
# -*- coding: utf-8 -*-


import httplib
import logging
import sys

import arrow
import webapp2
from google.appengine.api import memcache
from google.appengine.ext import deferred
from google.appengine.ext import ndb
from google.appengine.ext.ndb import blobstore

import mixins
import models
from . import base
from api.handlers import errors
from api.handlers import main


__all__ = [
    'Home',
    'Admin',
    'WarmUp',
    #'ExteriorImage',
]


class WarmUp(main.Health, base.BaseHandler):
  """Handler for warmup requests sent to /_ah/warmup."""

  def get(self, *args, **kwargs):
    """Print out health status to try and keep the frontend instance up."""
    status = httplib.OK
    self.response.status_int = status
    self.response.status_message = httplib.responses[status]
    self.response.write(self.services())


class Home(base.BaseHandler):

  template = 'lite.html'

  def get(self, *args, **kwargs):
    context = {
      'preload': {},
      'now': arrow.now(),
      'url': self.request.url,
    }
    self.render(self.context)
