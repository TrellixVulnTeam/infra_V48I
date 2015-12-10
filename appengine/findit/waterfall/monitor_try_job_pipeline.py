# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import time

from common import buildbucket_client
from model import wf_analysis_status
from model.wf_try_job import WfTryJob
from pipeline_wrapper import BasePipeline
from pipeline_wrapper import pipeline


class MonitorTryJobPipeline(BasePipeline):
  """A piepline for monitoring a tryjob and recording results when it's done."""

  # Arguments number differs from overridden method - pylint: disable=W0221
  def run(self, master_name, builder_name, build_number, try_job_id):
    assert try_job_id

    timeout_seconds = 2*60*60  # Timeout after 2 hours.
    deadline = time.time() + timeout_seconds

    already_set_started = False
    while True:
      error, build = buildbucket_client.GetTryJobs([try_job_id])[0]
      if error:  # pragma: no cover
        raise pipeline.Retry(
            'Error "%s" occurred. Reason: "%s"' % (error.message, error.reason))
      elif build.status == 'COMPLETED':
        try_job_result = WfTryJob.Get(master_name, builder_name, build_number)

        result = {
          'result': build.result,
          'url': build.url,
          'try_job_id': try_job_id,
        }
        if (try_job_result.results and
            try_job_result.results[-1]['try_job_id'] == try_job_id):
          try_job_result.results[-1].update(result)
        else:  # pragma: no cover
          try_job_result.results.append(result)

        try_job_result.status = wf_analysis_status.ANALYZED
        try_job_result.put()
        return try_job_result.results
      else:  # pragma: no cover
        if build.status == 'STARTED' and not already_set_started:
          try_job_result = WfTryJob.Get(master_name, builder_name, build_number)
          if (not try_job_result.results or
              try_job_result.results[-1]['try_job_id'] != try_job_id):
            try_job_result.status = wf_analysis_status.ANALYZING
            result = {
              'result': None,
              'url': build.url,
              'try_job_id': try_job_id,
            }
            try_job_result.results.append(result)
            try_job_result.put()
          already_set_started = True

        time.sleep(60)

      if time.time() > deadline:  # pragma: no cover
        logging.error('Try job %s timed out.', try_job_id)
        try_job_result.status = wf_analysis_status.ERROR
        try_job_result.put()
        return None