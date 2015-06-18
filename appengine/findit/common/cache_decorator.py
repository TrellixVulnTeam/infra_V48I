# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""This module provides a decorator to cache the results of a function.

  Examples:
  1. Decorate a function:
    @cache_decorator.Cached()
    def Test(a):
      return a + a

    Test('a')
    Test('a')  # Returns the cached 'aa'.

  2. Decorate a method in a class:
    class Downloader(object):
      def __init__(self, url, retries):
        self.url = url
        self.retries = retries

      @property
      def identifier(self):
        return self.url

      @cache_decorator.Cached():
      def Download(self, path):
        return urllib2.urlopen(self.url + '/' + path).read()

      d1 = Downloader('http://url', 4)
      d1.Download('path')

      d2 = Downloader('http://url', 5)
      d2.Download('path')  # Returned the cached downloaded data.
"""

import functools
import hashlib
import inspect
import pickle

from google.appengine.api import memcache


class Cacher(object):
  """An interface to cache and retrieve data.

  Subclasses should implement the Get/Set functions.
  TODO: Add a Delete function (default to no-op) if needed later.
  """
  def Get(self, key):
    """Returns the cached data for the given key if available.

    Args:
      key (str): The key to identify the cached data.
    """
    raise NotImplementedError()

  def Set(self, key, data, expire_time=0):
    """Cache the given data which is identified by the given key.

    Args:
      key (str): The key to identify the cached data.
      data (object): The python object to be cached.
      expire_time (int): Number of seconds from current time (up to 1 month).
    """
    raise NotImplementedError()


class MemCacher(Cacher):
  """An memcache-backed implementation of the interface Cacher.

  The data to be cached should be picklable.
  """
  def Get(self, key):
    return memcache.get(key)

  def Set(self, key, data, expire_time=0):
    memcache.set(key, data, time=expire_time)


def _DefaultKeyGenerator(func, args, kwargs):
  """Generates a key from the function and arguments passed to it.

  Args:
    func (function): An abitrary function.
    args (list): Positional arguments passed to ``func``.
    kwargs (dict): Keyword arguments passed to ``func``.

  Returns:
    A string to represent a call to the given function with the given arguments.
  """
  params = inspect.getcallargs(func, *args, **kwargs)
  for var_name in params:
    if not hasattr(params[var_name], 'identifier'):
      continue

    if callable(params[var_name].identifier):
      params[var_name] = params[var_name].identifier()
    else:
      params[var_name] = params[var_name].identifier

  return hashlib.md5(pickle.dumps(params)).hexdigest()


def Cached(namespace=None,
           expire_time=0,
           key_generator=_DefaultKeyGenerator,
           cacher=MemCacher()):
  """Returns a decorator to cache the decorated function's results.

  However, if the function returns None, empty list/dict, empty string, or other
  value that is evaluated as False, the results won't be cached.

  This decorator is to cache results of different calls to the decorated
  function, and avoid executing it again if the calls are equivalent. Two calls
  are equivalent, if the namespace is the same and the keys generated by the
  ``key_generator`` are the same.

  The usage of this decorator requires that:
  - If the default key generator is used, parameters passed to the decorated
    function should be picklable, or each of the parameter has an identifier
    property or method which returns picklable results.
  - If the default cacher is used, the returned results of the decorated
    function should be picklable.

  Args:
    namespace (str): A prefix to the key for the cache. Default to the
        combination of module name and function name of the decorated function.
    expire_time (int): Expiration time, relative number of seconds from current
        time (up to 1 month). Defaults to 0 -- never expire.
    key_generator (function): A function to generate a key to represent a call
        to the decorated function. Defaults to :func:`_DefaultKeyGenerator`.
    cacher (Cacher): An instance of an implementation of interface `Cacher`.
        Defaults to one of `MemCacher` which is based on memcache.

  Returns:
    The cached results or the results of a new run of the decorated function.
  """
  def GetPrefix(func, namespace):
    return namespace or '%s.%s' % (func.__module__, func.__name__)

  def Decorator(func):
    """Decorator to cache a function's results."""
    @functools.wraps(func)
    def Wrapped(*args, **kwargs):
      prefix = GetPrefix(func, namespace)
      key = '%s-%s' % (prefix, key_generator(func, args, kwargs))

      result = cacher.Get(key)
      if result is not None:
        return result

      result = func(*args, **kwargs)
      if result:
        cacher.Set(key, result, expire_time=expire_time)

      return result

    return Wrapped

  return Decorator