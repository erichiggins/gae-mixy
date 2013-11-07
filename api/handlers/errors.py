#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Base API handlers.
"""


import httplib


__all__ = [
    'Error',
    'FormValidationError',
]


class Error(Exception):
  """Base Exception for api/handlers."""

  def __init__(self, code=None, msg=None):
    self.code = code or httplib.INTERNAL_SERVER_ERROR
    self.msg = msg or httplib.responses[self.code]
    Exception.__init__(self, self.msg)

  def __str__(self):
    return repr([self.code, self.msg])


class FormValidationError(Error):
  """Form Validtion Exception for api/handlers."""

  def __init__(self, code=None, msg=None, errors=None):
    self.code = code or httplib.BAD_REQUEST
    self.msg = msg or httplib.responses[self.code]
    self.errors = errors or []
    Exception.__init__(self, self.msg)

  def __str__(self):
    return repr([self.code, self.msg, self.errors])
