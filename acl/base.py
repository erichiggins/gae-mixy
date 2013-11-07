#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Access Control List.
"""


import httplib
from collections import namedtuple


__all__ = [
    'ACL',
    'Permission',
    'Acl',
    'Perm',
    'Error',
    'NotFoundError',
    'UnauthorizedError',
    'ForbiddenError',
    'can_read_query',
    'can_read',
    'can_write',
    'can_search',
    'can_create',
]


ACL = namedtuple('ACL', ['owner', 'group', 'world'])
Permission = namedtuple('Permission', ['create', 'read', 'write', 'execute'])
# Compatibility.
Acl = ACL
Perm = Permission


class Error(Exception):
  """Base ACL error."""

  def __init__(self, code):
    self.code = code
    self.msg = httplib.responses[code]
    Exception.__init__(self, self.msg)

  def __str__(self):
    return repr([self.code, self.msg])


class NotFoundError(Error):
  """The item being access does not exist."""

  def __init__(self):
    Error.__init__(self, httplib.NOT_FOUND)


class UnauthorizedError(Error):
  """The current user is not authenticated."""

  def __init__(self):
    Error.__init__(self, httplib.UNAUTHORIZED)


class ForbiddenError(Error):
  """The current user does not have proper permission."""

  def __init__(self):
    Error.__init__(self, httplib.FORBIDDEN)


def has_group_permission(user, thing, permission, grp_prop, user_grp_prop='groups'):
  """Convenience function for checking group permissions."""
  # If group does not have permission, fail early.
  if not permission:
    raise ForbiddenError()
  # Check if user is a group member and group has permission.
  model_groups = getattr(thing, grp_prop, [])
  match_groups = list(set(model_groups).intersection(getattr(user, user_grp_prop)))
  if match_groups:
    return True
  # Permission failed.
  raise ForbiddenError()


# TODO(eric): Consider renaming to `can_query`.
def can_read_query(user, model, user_filter, grp_prop='groups'):
  """Check if a user can perform queries on this model class."""
  # TODO(eric): Also verify `execute` permission.
  # Check world permission.
  if model.acl.world.read:
    return True

  # User must exist and have an id from this point on.
  if not getattr(user, 'id', False):
    raise UnauthorizedError()

  # Admins can access whatever they want.
  if getattr(user, 'admin', False):
    return True

  # Note(eric): Cannot check if owner, since that is per-instance.
  # Check if user matches requested user filter.
  if user_filter == user.id:
    if model.acl.owner.read:
      return True
    else:
      raise ForbiddenError()

  # Check group permissions.
  return has_group_permission(user, model, model.acl.group.read, grp_prop)


def can_read(user, obj, owner_prop='created_by', grp_prop='groups'):
  """Check a user and an object to see if the user can read it."""
  # TODO(eric): Support async_get().
  # Check for existing object instance.
  if obj is None:
    raise NotFoundError()

  # Check world permission.
  if obj.acl.world.read:
    return True

  # User must exist and have an id from this point on.
  if not getattr(user, 'id', False):
    raise UnauthorizedError()

  # Admins can access whatever they want.
  if getattr(user, 'admin', False):
    return True

  # Check if owner and owner can read.
  if getattr(obj, owner_prop, None) == user.id:
    if obj.acl.owner.read:
      return True
    else:
      raise ForbiddenError()

  # Check group permissions.
  return has_group_permission(user, obj, obj.acl.group.read, grp_prop)


def can_write(user, obj, owner_prop='created_by', grp_prop='groups'):
  """Check a user and an object to see if the user can write it."""
  # TODO(eric): Support async_get().
  # Check for existing object instance.
  if obj is None:
    raise NotFoundError()

  # Check world permission.
  if obj.acl.world.write:
    return True

  # User must exist and have an id from this point on.
  if not getattr(user, 'id', False):
    raise UnauthorizedError()

  # Admins can access whatever they want.
  if getattr(user, 'admin', False):
    return True

  # Check if owner and owner can write.
  if getattr(obj, owner_prop, None) == user.id:
    if obj.acl.owner.write:
      return True
    else:
      raise ForbiddenError()

  # Check group permissions.
  return has_group_permission(user, obj, obj.acl.group.write, grp_prop)


def can_create(user, obj, grp_prop='groups'):
  """Check a user and model class to see if the user can create it."""
  # TODO(eric): Support async_get().
  # Check for existing object instance.
  if obj is None:
    raise NotFoundError()

  # Check world permission.
  if obj.acl.world.create:
    return True

  # User must exist and have an id from this point on.
  if not getattr(user, 'id', False):
    raise UnauthorizedError()

  # Admins can access whatever they want.
  if getattr(user, 'admin', False):
    return True

  # Check group permissions.
  return has_group_permission(user, obj, obj.acl.group.create, grp_prop)


def can_search(user, model, grp_prop='groups'):
  """Check if a user can perform queries on this model class."""
  # TODO(eric): Also verify `execute` permission.
  # Check world permission.
  if model.acl.world.read:
    return True

  # User must exist and have an id from this point on.
  if not getattr(user, 'id', False):
    raise UnauthorizedError()

  # Admins can access whatever they want.
  if getattr(user, 'admin', False):
    return True

  # Note(eric): Cannot check if owner, since that is per-instance.
  # TODO(eric): Check if owned by user.

  # Check group permissions.
  return has_group_permission(user, model, model.acl.group.read, grp_prop)
