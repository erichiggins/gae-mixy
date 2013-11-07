#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Forms for ToDo models.
"""


import logging

from wtforms import fields

from . import base


__all__ = [
    'ToDoForm',
]

class ToDo(base.BaseForm):
  """ToDo Model form."""
  task = base.StringField('Task')
  assignee = base.StringField('Assignee')
  due = base.DateField('Due')

  @classmethod
  def assign_data(cls, form, obj):
    """Populate a new Form instance with data from the fields."""
    obj.task = form.task.data
    obj.assignee = form.assignee.data
    obj.due = form.due.data
