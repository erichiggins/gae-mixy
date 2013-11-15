#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
User inventory API handlers.
"""


import httplib
import json

from google.appengine.ext import ndb

import acl
from api.handlers import errors


__all__ = [
    'BaseMixin',
]


class BaseMixin(object):
  """Base mixin that provides data to both API and HTML handlers."""

  form = None
  model = None
  owner_prop = 'created_by'
  grp_prop = 'groups'
  include = None
  exclude = None
  filters = []
  user = None
  user_filter = None

  @ndb.synctasklet
  def create_single(self, user, request, session=None):
    """Create a new instance."""
    acl.can_create(user, self.model, self.grp_prop)
    form = self.form(request, csrf_context=session)
    if not form.validate():
      # Raise bad request with error messages.
      raise errors.FormValidationError(errors=form.error_messages)
    # Use form method to populate values into new instance.
    instance = self.model(key=self.model.CreateKey())
    # Set owner id.
    setattr(instance, self.owner_prop, user.id)
    self.form.assign_data(form, instance)
    status = yield instance.put_async()
    raise ndb.Return(status, instance)

  @ndb.synctasklet
  def read_single(self, obj_id, user):
    """Read a single instance."""
    instance = yield self.model.get_by_id_async(obj_id)
    # Check permissions. Should raise exception upon failure.
    acl.can_read(user, instance, self.owner_prop, self.grp_prop)
    # Return 410 Gone if disabled=True.
    if getattr(instance, 'disabled', False):
      raise errors.Error(httplib.GONE)
    raise ndb.Return(instance)

  @ndb.synctasklet
  def update_single(self, obj_id, user, request, session=None):
    """Update a single instance."""
    instance = self.model.get_by_id(obj_id)
    # Check permissions. Should raise exception upon failure.
    acl.can_write(user, instance, self.owner_prop, self.grp_prop)
    form = self.form(request, instance, csrf_context=session)
    if not form.validate():
      # Raise bad request with error messages.
      raise errors.FormValidationError(errors=form.error_messages)
    form.populate_obj(instance)
    status = yield instance.put_async()
    raise ndb.Return(status, instance)

  @ndb.synctasklet
  def delete_single(self, obj_id, user):
    """Delete (disable) a single instance."""
    instance = yield self.model.get_by_id_async(obj_id)
    # Check permissions. Should raise exception upon failure.
    acl.can_write(user, instance, self.owner_prop, self.grp_prop)
    # TODO(eric): Actually delete in the future.
    # Disable instead of delete.
    status = instance.disable()
    raise ndb.Return(status, instance)

  def parse_filters(self, filter_list):
    """Parse the request filter list into a property name/value then apply."""
    filters = []
    for combo in filter_list:
      # Skip over invalid entries.
      if ':' not in combo:
        continue
      # Split by the first colon (:).
      prop, val = combo.split(':', 1)
      # Attempt to decode the value into Python natives (int/float/bool).
      try:
        val = json.loads(val)
      except ValueError:
        pass
      # Append to the filter list in Query fashion.
      filters.append(getattr(self.model, prop) == val)
    return filters

  def read_list(self, user, request):
    """Read a list of instances, returns a query."""
    filters = self.parse_filters(request.get_all('filter', self.filters))
    # Get user filter, defaults to current user.
    # Note: getattr avoids logged in users but keeps code in acl module.
    user_id = getattr(user, 'id', None)
    user_filter = request.get('user', self.user_filter or user_id)
    acl.can_read_query(user, self.model, user_filter, self.grp_prop)
    query = self.model.query(*filters)
    # Filter users.
    if user_filter != 'ALL':
      # Don't filter by user, check permissions.
      query.filter(ndb.GenericProperty(self.owner_prop) == user_filter)
    # TODO(eric): Add order properties.
    return query

  @property
  def title(self):
    return u''

  @property
  def description(self):
    return u''
