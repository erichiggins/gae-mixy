#!/usr/bin/env python
# -*- coding: utf-8 -*-


import webapp2
from google.appengine.ext import ereporter
from webapp2 import Route
from webapp2_extras.routes import PathPrefixRoute
from webapp2_extras.routes import RedirectRoute

import config
import api
import handlers


__all__ = [
  'urls',
  'app',
]


# Enable the exception logger in production only.
if not config.DEBUG:
  ereporter.register_logger()


urls = [
    # Handling of some restricted /_ah/ requests that GAE doesn't.
    Route('/_ah/warmup', handlers.WarmUp),

    # Note(eric): /api should point to latest version, but only one for now.
    PathPrefixRoute(r'/api<:(/1)?>', api.urls),

    # SimpleAuth paths.
    PathPrefixRoute('/auth', [
        Route('/<provider:\w+><:/?>',
              'handlers.AuthHandler:_simple_auth',
              'auth_signin'),
        Route('/<provider:\w+>/callback<:/?>',
              'handlers.AuthHandler:_auth_callback',
              'auth_callback'),
    ]),

    # Images or other binary/blob data.
    Route('/b/<blob_key:\w+><:/?>', handlers.Binary, 'binary'),

    Route('/signin<:/?>', handlers.SignIn),
    Route('/signout<:/?>', handlers.SignOut),
    Route('/reset<:/?>', handlers.ResetPassword),
    Route('/recover<:/?>', handlers.RecoverAccount),

    # Redirect previous URLs.
    RedirectRoute('/home<:/?>', redirect_to='/'),
    RedirectRoute('/account/signin<:/?>', redirect_to='/signin'),
    RedirectRoute('/account/signout<:/?>', redirect_to='/signout'),

    Route('/admin<:/?>', handlers.Admin),
    Route('/admin/<args:\w+><:/?>', handlers.Admin),

    Route('/', handlers.Home),
    Route('/<name><:/?>', handlers.JsApp),
    Route('/<name>/<opt><:/?>', handlers.JsApp),
    Route('/<name>/<opt>/<meta:.*>', handlers.JsApp),

]
app = webapp2.WSGIApplication(urls, debug=config.DEBUG, config=config.CONFIG)


def main():
  app.run()


if __name__ == '__main__':
  main()
