#!/usr/bin/env python
"""
ToDo API handlers.
"""


from . import base
from .. import mixins


__all__ = [
    'ToDo',
    'ToDoList',
    'ToDoProperty',
]


class ToDo(base.EntityHandler, mixins.ToDo):
  """Handler for a single ToDo Model."""
  pass


class ToDoList(base.MultiEntityHandler, mixins.ToDo):
  """Handler for multiple ToDo Models."""
  pass


class ToDo(base.EntityPropertyHandler, mixins.ToDo):
  """Handler for a single ToDo Model property."""
  pass
