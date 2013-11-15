#!/usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import with_statement
import httplib

import arrow
import jinja2
import logging
import os
import stripe
import webapp2
from webapp2_extras import jinja2 as wa2_jinja2

import acl
import forms
from api.handlers import base
from api.handlers import errors
from tools import common


__all__ = [
    'BaseHandler',
]


class BaseHandler(base.BaseHandler):
  """Base HTML handler."""

  def render(self, resp, status=httplib.OK):
    """Render the response as HTML."""
    resp.update({
        # Defaults go here.
        'account': self.account,
        'now': arrow.utcnow(),
        'url_version_id': base.get_url_version_id(),
        # Add redirect destination.
        'dest_url': str(self.request.get('dest_url', '')),
        # Add form errors from session, if any.
        'form_errors': self.session.pop('form_errors', []),
    })

    if 'preload' not in resp:
      resp['preload'] = {}
    # Add version id.
    resp['preload']['version_id'] = base.get_version_id()
    # Add a csrf_token.
    resp['preload']['csrf_token'] = self.generate_csrf_token()
    resp['preload']['account'] = {'id': getattr(self.account, 'id', None)}
    # Convert preload data to JSON str.
    resp['preload'] = common.ndb_json_dumps(resp['preload'])

    self.response.status_int = status
    self.response.status_message = httplib.responses[status]
    self.response.write(self.jinja2.render_template(self.template, **resp))

  def handle_exception(self, exception, debug=False):
    """Render the exception as HTML."""
    # Log the exception.
    logging.exception(exception)

    # Create response dictionary and status defaults.
    tpl = 'error.html'
    status = httplib.INTERNAL_SERVER_ERROR
    resp_dict = {
        'message': 'A server error occurred.',
    }
    url_parts = self.urlsplit()
    redirect_url = '%s?%s' % (url_parts[2], url_parts[4])

    # Use error code if a HTTPException, or generic 500.
    if isinstance(exception, webapp2.HTTPException):
      status = exception.code
      resp_dict['message'] = exception.detail
    elif isinstance(exception, errors.FormValidationError):
      #status = exception.code
      #resp_dict['message'] = exception.msg
      #resp_dict['errors'] = exception.errors
      self.session['form_errors'] = exception.errors
      # Redirect user to current view URL.
      return self.redirect(redirect_url)
    elif isinstance(exception, stripe.StripeError):
      #status = exception.http_status
      #resp_dict['errors'] = exception.json_body['error']['message']
      self.session['form_errors'] = [
          exception.json_body['error']['message']
      ]
      return self.redirect(redirect_url)
    elif isinstance(exception, (errors.Error, acl.Error)):
      status = exception.code
      resp_dict['message'] = exception.msg

    resp_dict['status'] = status

    # Render output.
    self.response.status_int = status
    self.response.status_message = httplib.responses[status]
    # Render the exception response into the error template.
    self.response.write(self.jinja2.render_template(tpl, **resp_dict))

  @webapp2.cached_property
  def jinja2(self):
    """Returns a Jinja2 renderer cached in the app registry."""
    jinja_config = {
        'environment_args': {
            'auto_reload': False,
            'extensions': [
                'jinja2.ext.autoescape',
                'jinja2.ext.with_',
                'jinja2htmlcompress.SelectiveHTMLCompress',
            ],
        },
    }
    return wa2_jinja2.Jinja2(app=self.app, config=jinja_config)
