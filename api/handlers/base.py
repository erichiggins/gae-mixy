#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Base API handlers.
"""


import hmac
import httplib
import json
import logging
import os
import urllib
import urlparse
from hashlib import sha1

import arrow
import webapp2
from google.appengine.api import app_identity
from google.appengine.api import memcache
from google.appengine.api import search
from google.appengine.api import urlfetch
from google.appengine.ext import ndb
from webapp2_extras import auth as wa2_auth
from webapp2_extras import sessions

import acl
import config
import forms
from . import errors
from tools import common


__all__ = [
    'get_application_id',
    'get_version_id',
    'get_url_version_id',
    'BaseHandler',
    'SearchHandler',
    'EntityHandler',
    'MultiEntityHandler',
    'EntityPropertyHandler',
    'ProxyHandler',
    'CachedProxyHandler',
]


def get_application_id():
  """Returns the app id from the app_identity service."""
  return app_identity.get_application_id()

def get_version_id():
  """Returns the current_version_id environment variable."""
  return os.environ.get('CURRENT_VERSION_ID', '0')

def get_url_version_id():
  """Returns a url-safe of the current_version_id environment variable."""
  return common.slugify(get_version_id())


class BaseHandler(webapp2.RequestHandler):

  CSRF_DELIMITER = ':'
  CSRF_HEADER = 'x-mixy-csrf-token'

  def initialize(self, request, response):
    super(BaseHandler, self).initialize(request, response)
    self.session_backend = 'datastore'

  def verify_origin(self):
    server_host = os.environ.get('DEFAULT_VERSION_HOSTNAME')
    request_host = self.request.headers.get('Host')
    request_referer = self.request.headers.get('Referer')
    if request_referer:
      request_referer = urlparse.urlsplit(request_referer)[1]
    else:
      request_referer = request_host
    logging.info('server: %s, request: %s', server_host, request_referer)
    if server_host and request_referer and server_host != request_referer:
      raise errors.Error(httplib.FORBIDDEN)

  def dispatch(self):
    """Dispatch the request."""
    # Get a session store for this request.
    self.session_store = sessions.get_store(request=self.request)
    # Note(eric): Forwards the method for RESTful support.
    self.forward_method()
    # Security headers.
    # https://www.owasp.org/index.php/List_of_useful_HTTP_headers
    self.response.headers['x-content-type-options'] = 'nosniff'
    self.response.headers['x-frame-options'] = 'SAMEORIGIN'
    self.response.headers['x-xss-protection'] = '1; mode=block'
    try:
      webapp2.RequestHandler.dispatch(self)  # Dispatch the request.
    finally:
      self.session_store.save_sessions(self.response)  # Save all sessions.
    # TODO(eric): Disabled for now because host is appspot.com in production.
    #self.verify_origin()

  def handle_exception(self, exception, debug=False):
    # Log the exception.
    logging.exception(exception)

    # Create response dictionary.
    status = httplib.INTERNAL_SERVER_ERROR
    resp_dict = {
        'message': 'A server error occurred.',
    }

    # Use error code if a HTTPException, or generic 500.
    if isinstance(exception, webapp2.HTTPException):
      status = exception.code
      resp_dict['message'] = exception.detail
    elif isinstance(exception, errors.FormValidationError):
      status = exception.code
      resp_dict['message'] = exception.msg
      resp_dict['errors'] = exception.errors
    elif isinstance(exception, (errors.Error, acl.Error)):
      status = exception.code
      resp_dict['message'] = exception.msg
    elif isinstance(exception, stripe.StripeError):
      status = exception.http_status
      resp_dict['errors'] = exception.json_body['error']['message']

    resp_dict['status'] = status

    self.response.content_type = 'application/json'
    self.response.status_int = status
    self.response.status_message = httplib.responses[status]
    # Send the exception response via JSON.
    common.ndb_json_dump(resp_dict, self.response)

  def get(self, *args, **kwargs):
    """Read."""
    self.abort(httplib.NOT_IMPLEMENTED)

  def post(self, *args, **kwargs):
    """Create."""
    self.abort(httplib.NOT_IMPLEMENTED)

  def put(self, *args, **kwargs):
    """Update."""
    self.abort(httplib.NOT_IMPLEMENTED)

  def delete(self, *args, **kwargs):
    """Delete."""
    self.abort(httplib.NOT_IMPLEMENTED)

  def head(self, *args, **kwargs):
    """Head calls should work, for some APIs like Twitter."""
    pass

  def urlsplit(self):
    """Return a tuple of the URL."""
    return urlparse.urlsplit(self.request.url)

  def path(self):
    """Returns the path of the current URL."""
    return self.urlsplit()[2]

  def forward_method(self):
    """Check for a method override param and change in the request."""
    valid = (None, 'get', 'post', 'put', 'delete', 'head', 'options')
    method = self.request.POST.get('__method__')
    if not method:  # Backbone's _method parameter.
      method = self.request.POST.get('_method')
    if method not in valid:
      logging.debug('Invalid method %s requested!', method)
      method = None
    logging.debug('Method being changed from %s to %s by request',
        self.request.route.handler_method, method)
    self.request.route.handler_method = method

  def add_message(self, value, level=None):
    """Add a message to the session."""
    # Note(eric): With multiple tabs, these may display in the wrong place.
    self.session.add_flash(value, level, key='_messages')

  def signin(self, user):
    """Sign a user in and set the session."""
    self.auth.set_session(self.auth.store.user_to_dict(user))

  def signout(self):
    """Sign the current user out and reset the session."""
    self.auth.unset_session()

  def render(self, resp, status=httplib.OK, json_kwargs=None):
    """Render the response as json."""
    callback = self.request.get('callback')
    pretty = self.request.get('pretty', None)
    if not json_kwargs:
      json_kwargs = {}
    if pretty is not None:
      json_kwargs['indent'] = 2

    self.response.content_type = 'application/json'
    self.response.status_int = status
    self.response.status_message = httplib.responses[status]
    if callback:
      self.response.out.write(callback + '(')
    common.ndb_json_dump(resp, self.response, **json_kwargs)
    if callback:
      self.response.out.write(')')

  def generate_csrf_token(self):
    """Generate a csrf token and store it in the user's session."""
    if 'csrf' not in self.session:
      self.session['csrf'] = sha1(os.urandom(64)).hexdigest()

    secret_key = config.CONFIG['csrf']['secret_key']
    time_limit = config.CONFIG['csrf']['time_limit']
    time_format = config.CONFIG['csrf']['time_format']

    csrf_key = self.session['csrf']
    if time_limit:
      expires = (arrow.now() + time_limit).format(time_format)
      csrf_build = '%s%s' % (csrf_key, expires)
    else:
      expires = ''
      csrf_build = csrf_key

    hmac_csrf = hmac.new(
        secret_key, csrf_build.encode('utf8'), digestmod=sha1)
    return '%s##%s' % (expires, hmac_csrf.hexdigest())

  def validate_csrf_token(self, token):
    """Attempt to validate the csrf token."""
    if not token or '##' not in token or 'csrf' not in self.session:
      raise errors.Error('CSRF token missing')

    secret_key = config.CONFIG['csrf']['secret_key']
    time_limit = config.CONFIG['csrf']['time_limit']
    time_format = config.CONFIG['csrf']['time_format']

    expires, hmac_csrf = token.split('##')
    csrf_key = self.session['csrf']
    check_val = (csrf_key + expires).encode('utf8')

    hmac_compare = hmac.new(secret_key, check_val, digestmod=sha1)
    if hmac_compare.hexdigest() != hmac_csrf:
      raise errors.Error('CSRF token mismatch')

    if time_limit:
      now_formatted = arrow.now().format(time_format)
      if now_formatted > expires:
        raise errors.Error('CSRF token expired')
    return True

  def verify_csrf(self):
    csrf_token = self.request.headers.get(self.CSRF_HEADER)
    if not self.validate_csrf_token(csrf_token):
      raise errors.Error(httplib.FORBIDDEN)

  @property
  def auth(self):
    return wa2_auth.get_auth()

  @property
  def session(self):
    """Returns a session using the default cookie key."""
    return self.session_store.get_session(backend=self.session_backend)

  @property
  @ndb.synctasklet
  def account(self):
    """Non-cached account property."""
    user_dict = self.auth.get_user_by_session() or {}
    user_id = user_dict.get('user_id', None)
    user = None
    if user_id:
      user = yield self.auth.store.user_model.get_by_id_async(user_id)
    raise ndb.Return(user)


class SearchHandler(BaseHandler):

  #index = None
  #fields = None
  owner_prop = 'created_by'
  grp_prop = 'groups'

  def get(self, *args, **kwargs):
    acl.can_search(self.account, self.model, self.grp_prop)
    query = self.request.get('query')
    cursor = self.request.get('cursor', '')
    results = self.do_search(query, cursor)
    instances = self.format_documents(results.results)
    #resp = self.typeahead_format(instances)
    resp = self.bootstrap_format(results, instances)
    self.render(resp)

  def do_search(self, query, cursor=None):
    query_opts = search.QueryOptions(
        limit=15)
    query_instance = search.Query(query_string=query, options=query_opts)
    return self.index.search(query_instance)

  def bootstrap_format(self, results, instances):
    resp = {
      'results': instances,
      'number_found': results.number_found,
      #'cursor': getattr(results.cursor, 'web_safe_string', None),
    }
    return resp

  def typeahead_format(self, results):
    """Once typeahead.js supports event callbacks, this can be used."""
    resp = []
    for result in results:
      datum = {
          'id': result['id'],
          'value': result['title'],
          'tokens': result['title'].split(),
      }
      resp.append(datum)
    return resp

  def format_documents(self, documents):
    results = []
    for doc in documents:
      fmt_doc = {'id': doc.doc_id}
      for field in doc.fields:
        fmt_doc[field.name] = field.value
      results.append(fmt_doc)
    return results


class SingletonHandler(BaseHandler):

  owner_prop = 'created_by'
  grp_prop = 'groups'

  def get(self, obj_id, **kwargs):
    instance = self.read_single(obj_id, self.account)
    if self.include or self.exclude:
      instance = instance.to_dict(include=self.include, exclude=self.exclude)
    self.render(instance)

  def put(self, obj_id, **kwargs):
    """Update."""
    self.verify_csrf()
    # TODO(eric): Check for string before doing the following conversion.
    # Convert the JSON request string to a MultiDict.
    request_dict = forms.body_to_multidict(self.request.body)
    status, instance = self.update_single(
        obj_id, self.account, request_dict, self.session)
    if self.include or self.exclude:
      instance = instance.to_dict(include=self.include, exclude=self.exclude)
    self.render(instance, httplib.ACCEPTED)

  def delete(self, obj_id, **kwargs):
    """Delete."""
    self.verify_csrf()
    status, instance = self.delete_single(obj_id, self.account)
    if self.include or self.exclude:
      instance = instance.to_dict(include=self.include, exclude=self.exclude)
    self.render(instance, httplib.ACCEPTED)


class PropertyHandler(SingletonHandler):

  def get(self, obj_id, prop, **kwargs):
    """Read."""
    instance = self.read_single(obj_id, self.account)
    # TODO(eric): None may indicate existing property. Consider exception.
    resp = {prop: getattr(instance, prop, None)}
    self.render(resp)

  def put(self, *args, **kwargs):
    """Update."""
    self.verify_csrf()
    raise NotImplementedError

  def delete(self, *args, **kwargs):
    """Delete."""
    self.verify_csrf()
    raise NotImplementedError


class ListHandler(SingletonHandler):

  @ndb.synctasklet
  def get(self, *args, **kwargs):
    """Read."""
    query = self.read_list(self.account, self.request)
    if self.include or self.exclude:
      opts = {'include': self.include, 'exclude': self.exclude}
      callback = lambda x: x.to_dict(**opts)
      query = yield query.map_async(callback)

    self.render(query)

  def post(self, *args, **kwargs):
    """Create."""
    self.verify_csrf()
    # TODO(eric): Check for string before doing the following conversion.
    # Convert the JSON request string to a MultiDict.
    request_dict = forms.body_to_multidict(self.request.body)
    status, instance = self.create_single(
        self.account, request_dict, self.session)
    if self.include or self.exclude:
      instance = instance.to_dict(include=self.include, exclude=self.exclude)
    self.render(instance, httplib.CREATED)

  def put(self, *args, **kwargs):
    """Update."""
    raise NotImplementedError

  def delete(self, *args, **kwargs):
    """Delete."""
    raise NotImplementedError


class ProxyHandler(BaseHandler):

  remote_url = ''

  @login_required
  def get(self, *args, **kwargs):
    params = urllib.urlencode(self.request.params)
    resp = urlfetch.fetch(self.remote_url + params)
    content_dict = json.loads(resp.content)
    self.render(content_dict, resp.status_code)


class CachedProxyHandler(BaseHandler):

  # These need to be overridden.
  expire = 3600
  remote_url = None
  memcache_key = None

  @login_required
  def get(self, *args, **kwargs):
    status, resp = self.sync(*args, **kwargs)
    self.render(resp, status)

  def sync(self, *args, **kwargs):
    """Makes a call, returns a value, pulls from cache or saves to cache."""
    assert self.memcache_key
    raw_data = memcache.get(self.memcache_key)
    if raw_data is not None:
      logging.info('Cached response found for %s', self.remote_url)
      return httplib.OK, self.parse(raw_data)
    else:
      # Fetch from remote server.
      status, raw_data = self.fetch(*args, **kwargs)
      # Validate response.
      if status != httplib.OK or not self.validate(raw_data):
        return status, raw_data
      # Store.
      memcache.add(self.memcache_key, raw_data, self.expire)
      # TODO(eric): task queue to save raw_data to datastore.
      # Return.
      return status, self.parse(raw_data)

  def fetch(self, *args, **kwargs):
    logging.info('Fetching remote data for %s', self.remote_url)
    resp = urlfetch.fetch(self.remote_url)
    json_content = json.loads(resp.content)
    return resp.status_code, json_content

  def validate(self, raw_data):
    return raw_data is not None

  def parse(self, raw_data):
    return raw_data
