# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""This module is to provide Findit service APIs through Cloud Endpoints:

Current APIs include:
1. Analysis of compile/test failures in Chromium waterfalls.
   Analyzes failures and detects suspected CLs.
"""

import json
import logging

import endpoints
from google.appengine.api import taskqueue
from protorpc import messages
from protorpc import remote

from common import appengine_util
from common import constants
from model.wf_analysis import WfAnalysis
from waterfall import buildbot
from waterfall import waterfall_config


# This is used by the underlying ProtoRpc when creating names for the ProtoRPC
# messages below. This package name will show up as a prefix to the message
# class names in the discovery doc and client libraries.
package = 'FindIt'


# These subclasses of Message are basically definitions of Protocol RPC
# messages. https://cloud.google.com/appengine/docs/python/tools/protorpc/
class _BuildFailure(messages.Message):
  master_url = messages.StringField(1, required=True)
  builder_name = messages.StringField(2, required=True)
  build_number = messages.IntegerField(3, variant=messages.Variant.INT32,
                                       required=True)
  # All failed steps of the build reported by the client.
  failed_steps = messages.StringField(4, repeated=True, required=False)


class _BuildFailureCollection(messages.Message):
  """Represents a request from a client, eg. builder_alerts."""
  builds = messages.MessageField(_BuildFailure, 1, repeated=True)


class _SuspectedCL(messages.Message):
  repo_name = messages.StringField(1, required=True)
  revision = messages.StringField(2, required=True)
  commit_position = messages.IntegerField(3, variant=messages.Variant.INT32)


class _BuildFailureAnalysisResult(messages.Message):
  master_url = messages.StringField(1, required=True)
  builder_name = messages.StringField(2, required=True)
  build_number = messages.IntegerField(3, variant=messages.Variant.INT32,
                                       required=True)
  step_name = messages.StringField(4, required=True)
  is_sub_test = messages.BooleanField(5, variant=messages.Variant.BOOL,
                                      required=True)
  test_name = messages.StringField(6)
  first_known_failed_build_number = messages.IntegerField(
      7, variant=messages.Variant.INT32)
  suspected_cls = messages.MessageField(_SuspectedCL, 8, repeated=True)


class _BuildFailureAnalysisResultCollection(messages.Message):
  """Represents a response to the client, eg. builder_alerts."""
  results = messages.MessageField(_BuildFailureAnalysisResult, 1, repeated=True)


def _TriggerNewAnalysesOnDemand(builds_to_check):
  """Pushes a task to run on the backend to trigger new analyses on demand."""
  target = appengine_util.GetTargetNameForModule(constants.WATERFALL_BACKEND)
  payload = json.dumps({'builds': builds_to_check})
  taskqueue.add(
      url=constants.WATERFALL_TRIGGER_ANALYSIS_URL, payload=payload,
      target=target, queue_name=constants.WATERFALL_SERIAL_QUEUE)


# Create a Cloud Endpoints API.
# https://cloud.google.com/appengine/docs/python/endpoints/create_api
@endpoints.api(name='findit', version='v1', description='FindIt API')
class FindItApi(remote.Service):
  """FindIt API v1."""

  def _GenerateBuildFailureAnalysisResult(
      self, build, suspected_cls_in_result, step_name,
      first_failure, test_name=None):
    suspected_cls = []
    for suspected_cl in suspected_cls_in_result:
      suspected_cls.append(_SuspectedCL(
          repo_name=suspected_cl['repo_name'],
          revision=suspected_cl['revision'],
          commit_position=suspected_cl['commit_position']))

    return _BuildFailureAnalysisResult(
        master_url=build.master_url,
        builder_name=build.builder_name,
        build_number=build.build_number,
        step_name=step_name,
        is_sub_test=test_name is not None,
        test_name=test_name,
        first_known_failed_build_number=first_failure,
        suspected_cls=suspected_cls)

  @endpoints.method(
      _BuildFailureCollection, _BuildFailureAnalysisResultCollection,
      path='buildfailure', name='buildfailure')
  def AnalyzeBuildFailures(self, request):
    """Returns analysis results for the given build failures in the request.

    Analysis of build failures will be triggered automatically on demand.

    Args:
      request (_BuildFailureCollection): A list of build failures.

    Returns:
      _BuildFailureAnalysisResultCollection
      A list of analysis results for the given build failures.
    """
    results = []
    builds_to_check = []

    for build in request.builds:
      master_name = buildbot.GetMasterNameFromUrl(build.master_url)
      if not (master_name and waterfall_config.MasterIsSupported(master_name)):
        continue

      builds_to_check.append({
          'master_name': master_name,
          'builder_name': build.builder_name,
          'build_number': build.build_number,
          'failed_steps': build.failed_steps,
      })

      # If the build failure was already analyzed and a new analysis is
      # scheduled to analyze new failed steps, the returned WfAnalysis will
      # still have the result from last completed analysis.
      # If there is no analysis yet, no result is returned.
      analysis = WfAnalysis.Get(
          master_name, build.builder_name, build.build_number)
      if not analysis:
        continue

      if analysis.failed or not analysis.result:
        # Bail out if the analysis failed or there is no result yet.
        continue

      for failure in analysis.result['failures']:
        if not failure['suspected_cls'] and not failure.get('tests'):
          continue

        if failure.get('tests'):
          for test in failure['tests']:
            if not test['suspected_cls']:
              continue
            results.append(self._GenerateBuildFailureAnalysisResult(
                build, test['suspected_cls'], failure['step_name'],
                test['first_failure'], test['test_name']))

        else:
          results.append(self._GenerateBuildFailureAnalysisResult(
              build, failure['suspected_cls'], failure['step_name'],
              failure['first_failure']))

    logging.info('%d build failure(s), while %d are supported',
                 len(request.builds), len(builds_to_check))
    try:
      _TriggerNewAnalysesOnDemand(builds_to_check)
    except Exception:  # pragma: no cover.
      # If we fail to post a task to the task queue, we ignore and wait for next
      # request.
      logging.exception('Failed to trigger new analyses on demand.')

    return _BuildFailureAnalysisResultCollection(results=results)
