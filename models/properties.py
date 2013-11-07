#!/usr/bin/env python
# -*- coding: utf-8 -*-


from google.appengine.ext import ndb


__all__ = [
    'BoundedFloatProperty',
    'BoundedIntegerProperty',
]


class BoundedFloatProperty(ndb.FloatProperty):

  def __init__(self, bounds, **kwargs):
    assert len(bounds) == 2
    min_val, max_val = bounds
    assert isinstance(min_val, (int, float))
    assert isinstance(max_val, (int, float))
    assert min_val < max_val
    self._min = min_val
    self._max = max_val
    super(BoundedFloatProperty, self).__init__(**kwargs)

  def _validate(self, value):
    assert isinstance(value, (int, float))
    assert value <= self._max
    assert value >= self._min


class BoundedIntegerProperty(ndb.IntegerProperty):

  def __init__(self, bounds, **kwargs):
    assert len(bounds) == 2
    min_val, max_val = bounds
    assert isinstance(min_val, int)
    assert isinstance(max_val, int)
    assert min_val < max_val
    self._min = min_val
    self._max = max_val
    super(BoundedIntegerProperty, self).__init__(**kwargs)

  def _validate(self, value):
    assert isinstance(value, int)
    assert value <= self._max
    assert value >= self._min
