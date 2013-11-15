#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""URL mapping for JSON API handlers."""


__author__ = 'Eric Higgins'
__copyright__ = 'Copyright 2013, Eric Higgins'
__version__ = '0.0.1'
__email__ = 'erichiggins@gmail.com'


from webapp2 import Route
from webapp2_extras.routes import PathPrefixRoute

from . import handlers


__all__ = ['urls']


urls = [
    Route(r'/health<:/?>', handlers.Health),
    Route(r'/version<:/?>', handlers.Version),

    Route('/appstats', handlers.AppStatsList),
    PathPrefixRoute('/appstats', [
        Route('/', handlers.AppStatsList),
        Route(r'/<timestamp:\w+><:/?>', handlers.AppStats),
    ]),

    # Sample routing for developer reference.
    Route('/todos', handlers.ToDoList),
    PathPrefixRoute('/todos', [
        Route('/', handlers.ToDoList),
        Route(r'/<obj_id:\w+><:/?>', handlers.ToDo),
        Route(r'/<obj_id:\w+>/<prop:\w+><:/?>', handlers.ToDoProperty),
    ]),

]
