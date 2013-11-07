#!/usr/bin/env python
"""
Main API handlers.
"""


import httplib
import json
import logging

import arrow
import webapp2
from google.appengine.api import capabilities

import forms
import models
from . import base
from tools import appstats_serializer


__all__ = [
    'AppStats',
    'AppStatsList',
    'Health',
    'Version',
]


class AppStats(base.BaseHandler):
  """Return output from AppStats."""

  # TODO(eric): Restrict to admins only.
  #@base.admin_required
  def get(self, timestamp, *args, **kwargs):
    full_proto = appstats_serializer.load_full_proto_from_timestamp(timestamp)
    resp = appstats_serializer.request_stats_to_dict(full_proto)
    self.render(resp)


class AppStatsList(base.BaseHandler):
  """Return output from AppStats."""

  # TODO(eric): Restrict to admins only.
  #@base.admin_required
  def get(self, *args, **kwargs):
    resp = appstats_serializer.appstats_to_dict(summaries_only=True)
    self.render(resp)


class Health(base.BaseHandler):
  """Return a list of services and their status."""

  def get(self, *args, **kwargs):
    resp = {
        'services': self.services(),
    }
    self.render(resp)

  def services(self):
    """Return the status and admin message list for all available services."""
    blobstore_api = capabilities.CapabilitySet('blobstore')
    datastore_read_api = capabilities.CapabilitySet('datastore_v3')
    datastore_write_api = capabilities.CapabilitySet('datastore_v3', ['write'])
    mail_api = capabilities.CapabilitySet('mail')
    memcache_api = capabilities.CapabilitySet('memcache')
    taskqueue_api = capabilities.CapabilitySet('taskqueue')
    urlfetch_api = capabilities.CapabilitySet('urlfetch')
    return [
        {'blobstore': {
            'enabled': blobstore_api.is_enabled(),
            'message': blobstore_api.admin_message(),
        }},
        {'datastore_read': {
            'enabled': datastore_read_api.is_enabled(),
            'message': datastore_read_api.admin_message(),
        }},
        {'datastore_write': {
            'enabled': datastore_write_api.is_enabled(),
            'message': datastore_write_api.admin_message(),
        }},
        {'mail': {
            'enabled': mail_api.is_enabled(),
            'message': mail_api.admin_message(),
        }},
        {'memcache': {
            'enabled': memcache_api.is_enabled(),
            'message': memcache_api.admin_message(),
        }},
        {'taskqueue': {
            'enabled': taskqueue_api.is_enabled(),
            'message': taskqueue_api.admin_message(),
        }},
        {'urlfetch': {
            'enabled': urlfetch_api.is_enabled(),
            'message': urlfetch_api.admin_message(),
        }},
    ]


class Version(base.BaseHandler):
  """Returns the current app version."""

  def get(self, *args, **kwargs):
    resp = {
        'version': self.get_version_id(),
    }
    self.render(resp)
