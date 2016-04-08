# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import json

from common import buildbucket_client
from common.git_repository import GitRepository
from model import analysis_status
from model.wf_try_job import WfTryJob
from pipeline_wrapper import pipeline_handlers
from waterfall.test import wf_testcase
from waterfall.try_job_pipeline import TryJobPipeline
from waterfall.try_job_type import TryJobType


class TryJobPipelineTest(wf_testcase.WaterfallTestCase):
  app_module = pipeline_handlers._APP

  def _Mock_TriggerTryJobs(self, responses):
    def MockedTriggerTryJobs(*_):
      try_job_results = []
      for response in responses:
        if response.get('error'):  # pragma: no cover
          try_job_results.append((
              buildbucket_client.BuildbucketError(response['error']), None))
        else:
          try_job_results.append((
              None, buildbucket_client.BuildbucketBuild(response['build'])))
      return try_job_results
    self.mock(buildbucket_client, 'TriggerTryJobs', MockedTriggerTryJobs)

  def _Mock_GetTryJobs(self, build_id):
    def MockedGetTryJobs(*_):
      data = {
          '1': {
              'build': {
                  'id': '1',
                  'url': 'url',
                  'status': 'COMPLETED',
                  'result_details_json': json.dumps({
                      'properties': {
                          'report': {
                              'result': {
                                  'rev1': 'passed',
                                  'rev2': 'failed'
                              },
                              'metadata': {
                                  'regression_range_size': 2
                              }
                          }
                      }
                  })
              }
          },
          '3': {
              'error': {
                  'reason': 'BUILD_NOT_FOUND',
                  'message': 'message',
              }
          }
      }
      try_job_results = []
      build_error = data.get(build_id)
      if build_error.get('error'):  # pragma: no cover
        try_job_results.append((
            buildbucket_client.BuildbucketError(build_error['error']), None))
      else:
        try_job_results.append((
            None, buildbucket_client.BuildbucketBuild(build_error['build'])))
      return try_job_results
    self.mock(buildbucket_client, 'GetTryJobs', MockedGetTryJobs)

  def _Mock_GetChangeLog(self, revision):
    def MockedGetChangeLog(*_):
      class MockedChangeLog(object):

        def __init__(self, commit_position, code_review_url):
          self.commit_position = commit_position
          self.code_review_url = code_review_url

      mock_change_logs = {}
      mock_change_logs['rev2'] = MockedChangeLog('2', 'url_2')
      return mock_change_logs.get(revision)
    self.mock(GitRepository, 'GetChangeLog', MockedGetChangeLog)

  def testSuccessfullyScheduleNewTryJobForCompile(self):
    master_name = 'm'
    builder_name = 'b'
    build_number = 1

    responses = [
        {
            'build': {
                'id': '1',
                'url': 'url',
                'status': 'SCHEDULED',
            }
        }
    ]

    self._Mock_TriggerTryJobs(responses)
    self._Mock_GetTryJobs('1')
    self._Mock_GetChangeLog('rev2')

    WfTryJob.Create(master_name, builder_name, build_number).put()

    root_pipeline = TryJobPipeline(
        master_name, builder_name, build_number, 'rev1', 'rev2', ['rev2'],
        TryJobType.COMPILE, [])
    root_pipeline.start()
    self.execute_queued_tasks()

    try_job = WfTryJob.Get(master_name, builder_name, build_number)

    expected_try_job_results = [
        {
            'report': {
                'result': {
                    'rev1': 'passed',
                    'rev2': 'failed'
                },
                'metadata': {
                    'regression_range_size': 2
                }
            },
            'url': 'url',
            'try_job_id': '1',
            'culprit': {
                'compile': {
                    'revision': 'rev2',
                    'commit_position': '2',
                    'review_url': 'url_2'
                }
            }
        }
    ]
    self.assertEqual(expected_try_job_results, try_job.compile_results)

  def testPipelineAbortedWithTryJobResult(self):
    master_name = 'm'
    builder_name = 'b'
    build_number = 1

    WfTryJob.Create(master_name, builder_name, build_number).put()

    root_pipeline = TryJobPipeline(
        master_name, builder_name, build_number, 'rev1', 'rev2', ['rev2'],
        TryJobType.COMPILE, [])
    root_pipeline._LogUnexpectedAbort(True)

    try_job = WfTryJob.Get(master_name, builder_name, build_number)
    self.assertEqual(analysis_status.ERROR, try_job.status)

  def testPipelineAbortedWithOutTryJobResult(self):
    master_name = 'm'
    builder_name = 'b'
    build_number = 1

    root_pipeline = TryJobPipeline(
        master_name, builder_name, build_number, 'rev1', 'rev2', ['rev2'],
        TryJobType.COMPILE, [])
    root_pipeline._LogUnexpectedAbort(True)

    try_job = WfTryJob.Get(master_name, builder_name, build_number)

    self.assertIsNone(try_job)
