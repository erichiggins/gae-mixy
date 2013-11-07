#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ToDo API handlers.
"""


import forms
import models
from . import base


__all__ = [
    'ToDo',
]


class ToDo(base.BaseMixin):
  form = forms.ToDoForm
  model = models.ToDo
