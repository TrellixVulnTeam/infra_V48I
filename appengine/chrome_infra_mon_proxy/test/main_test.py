# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import os
import urllib2
import webtest

from google.appengine.api import taskqueue, users
from testing_utils import testing

import common
import main
from components import auth


class MonacqHandlerTest(testing.AppengineTestCase):

  @property
  def app_module(self):
    return main.app

  def setUp(self):
    super(MonacqHandlerTest, self).setUp()
    # Disable auth module checks.
    self.mock(users, 'get_current_user',
              lambda: users.User('test@user.com', 'auth_domain'))
    self.mock(main.MonacqHandler, 'xsrf_token_enforce_on', [])
    self.mock(auth, 'is_group_member', lambda _: True) # pragma: no branch

  def tearDown(self):
    super(MonacqHandlerTest, self).tearDown()

  def test_require_group_membership(self):
    # This is a smoke test for coverage. The function is otherwise trivial.
    self.mock(os, 'environ', {'SERVER_SOFTWARE': 'Development server'})
    main.require_group_membership('foo')
    self.mock(os, 'environ', {'SERVER_SOFTWARE': 'GAE production server'})
    main.require_group_membership('foo')

  def test_get(self):
    # GET request is not allowed.
    with self.assertRaises(webtest.AppError) as cm:
      self.test_app.get('/monacq')
    logging.info('exception = %s', cm.exception)
    self.assertIn('405', str(cm.exception))

  def test_post(self):
    # self.mock(taskqueue, 'add', lambda *_args, **_kw: None)
    self.mock(urllib2, 'urlopen', lambda _: None)
    # Dev appserver.
    self.mock(os, 'environ', {'SERVER_SOFTWARE': 'Development server'})
    self.test_app.post('/monacq', 'deadbeafdata')
    # Production server.
    self.mock(os, 'environ', {'SERVER_SOFTWARE': 'GAE production server'})
    self.test_app.post('/monacq', 'deadbeafdata')


class MainHandlerTest(testing.AppengineTestCase):

  @property
  def app_module(self):
    return main.app

  def test_get(self):
    response = self.test_app.get('/')
    logging.info('response = %s', response)
    self.assertEquals(200, response.status_int)