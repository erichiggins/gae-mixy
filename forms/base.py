#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Base forms.
"""


import logging
import json

import wtforms
from webob import multidict
from wtforms import fields
from wtforms import validators
from wtforms import widgets
from wtforms.ext.csrf import session as wtforms_session

import config

__all__ = [
    'DATA_REQUIRED',
    'INPUT_REQUIRED',
    'REQUIRED',
    'Error',
    'FormError',
    'TextInput',
    'FloatField',
    'IntegerField',
    'StringField',
    'ComputedStringField',
    'BaseFormMixin',
    'BaseForm',
    'SecureBaseForm',
    'json_to_form',
    'body_to_multidict',
    'HideFields',
    'GetBindingMap',
]


DATA_REQUIRED = validators.data_required()
INPUT_REQUIRED = validators.input_required()
REQUIRED = DATA_REQUIRED


def json_to_form(form_dict, sep=u'_', pre=u'', _ls=u'-'):
  """Convert a json dictionary to match the flat form fieldnames."""
  flat = []
  for key, val in form_dict.iteritems():
    key_name = pre + key if pre else key
    if isinstance(val, dict):
      leaf = json_to_form(val, sep=sep, pre=key_name + sep)
      flat += leaf
    elif isinstance(val, list) and (len(val) and isinstance(val[0], dict)):
      for i, row in enumerate(val):
        row_key = _ls.join([key_name, str(i)])
        leaf = json_to_form(row, sep=sep, pre=row_key + _ls)
        flat += leaf
    else:
      node = (key_name, val)
      if key_name != u'id' and val is not None:
        flat.append(node)
  return flat


def body_to_multidict(request_body):
  request_dict = json.loads(request_body)
  flat_request = json_to_form(request_dict)
  return multidict.MultiDict(flat_request)


class Error(Exception):
  pass


class FormError(Error):
  pass


def HideFields(form):
  """Converts form fields to HiddenInput in a forcefully hacky way."""
  for name, field in form._fields.iteritems():
    if field.type == 'FormField':
      HideFields(field)
    else:
      getattr(form, name).widget = widgets.HiddenInput()


def GetBindingMap(form):
  bindings = {}
  for name, field in form._fields.items():
    if isinstance(field, fields.FormField):
      bindings[name] = GetBindingMap(field)
    elif isinstance(field, fields.FieldList):
      bindings[name] = [GetBindingMap(x) for x in field]
    else:
      bindings[name] = {
          'selector': str('#' + field.id),  # str avoids using json module.
      }
  return bindings


class TextInput(widgets.TextInput):

  def __call__(self, *args, **kwargs):
    kwargs.pop('append', None)
    kwargs.pop('prepend', None)
    return super(TextInput, self).__call__(*args, **kwargs)


class FloatField(fields.FloatField):
  widget = TextInput()


class IntegerField(fields.IntegerField):
  widget = TextInput()


class StringField(fields.StringField):
  widget = TextInput()


class ComputedStringField(fields.StringField):
  """Use on computed fields and forms with mixins to skip populate_obj."""

  def populate_obj(self, obj, name):
    """Do nothing, intentionally."""
    pass


class BooleanField(fields.BooleanField):
  """BooleanField that works with False values. WTForms version is dumb."""

  def process_formdata(self, valuelist):
    """False if it doesn't exist, other values are bool cast."""
    self.data = bool(valuelist[0]) if valuelist else False


class BaseFormMixin(object):
  """Mixin used to add specific properties to the Base forms."""

  @classmethod
  def assign_data(cls, form, obj):
    """Assign form field data to the object when creating instances."""
    # Should be implemented by each form class.
    raise NotImplementedError

  @property
  def error_messages(self):
    """Collapse nested errors into a list of strings."""
    fmt = u'%s: %s'
    messages = [fmt % (x.label.text, y)
                for x in self for y in self.errors.get(x.name, []) if y]
    logging.debug(messages)
    return messages

  def HideFields(self):
    HideFields(self)

  @property
  def model_bindings(self):
    return GetBindingMap(self)


class BaseForm(wtforms.form.Form, BaseFormMixin):
  """Regular form, no CSRF."""
  pass


class SecureBaseForm(wtforms_session.SessionSecureForm, BaseFormMixin):
  """CSRF protected form."""

  SECRET_KEY = config.CONFIG['wtforms.csrf']['secret_key']
  TIME_LIMIT = None  # Note(eric): This prevents CSRF expiration.
