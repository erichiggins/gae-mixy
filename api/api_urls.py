#!/usr/bin/env python
# -*- coding: utf-8 -*-


from webapp2 import Route
from webapp2_extras.routes import PathPrefixRoute

from . import handlers


__all__ = ['urls']


urls = [
    Route('/health<:/?>', handlers.Health),
    Route('/version<:/?>', handlers.Version),

    Route('/appstats', handlers.AppStatsList),
    PathPrefixRoute('/appstats', [
        Route('/', handlers.AppStatsList),
        Route('/<timestamp:\w+><:/?>', handlers.AppStats),
    ]),

    # Sample routing for developer reference.
    Route('/todos', handlers.ToDoList),
    PathPrefixRoute('/todos', [
        Route('/', handlers.ToDoList),
        Route('/<obj_id:\w+><:/?>', handlers.ToDo),
        Route('/<obj_id:\w+>/<prop:\w+><:/?>', handlers.ToDoProperty),
    ]),

]
