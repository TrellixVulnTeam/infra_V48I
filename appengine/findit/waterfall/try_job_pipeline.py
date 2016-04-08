# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from pipeline_wrapper import BasePipeline
from model import analysis_status
from model.wf_try_job import WfTryJob
from waterfall.identify_try_job_culprit_pipeline import (
    IdentifyTryJobCulpritPipeline)
from waterfall.monitor_try_job_pipeline import MonitorTryJobPipeline
from waterfall.schedule_try_job_pipeline import ScheduleTryJobPipeline


class TryJobPipeline(BasePipeline):
  """Root pipeline to start a try job on current build."""

  def __init__(
      self, master_name, builder_name, build_number,
      good_revision, bad_revision, blame_list, try_job_type,
      compile_targets=None, targeted_tests=None):
    super(TryJobPipeline, self).__init__(
        master_name, builder_name, build_number, good_revision, bad_revision,
        blame_list, try_job_type, compile_targets, targeted_tests)
    self.master_name = master_name
    self.builder_name = builder_name
    self.build_number = build_number

  def _LogUnexpectedAbort(self, was_aborted):
    """Marks the WfTryJob status as error, indicating that it was aborted.

    Args:
      was_aborted (bool): True if the pipeline was aborted due to some error
      or exception, otherwise False.
    """
    if was_aborted:
      try_job_result = WfTryJob.Get(
          self.master_name, self.builder_name, self.build_number)
      if try_job_result:  # In case the result is deleted manually.
        try_job_result.status = analysis_status.ERROR
        try_job_result.put()

  def finalized(self):
    """Finalizes this Pipeline after execution."""
    self._LogUnexpectedAbort(self.was_aborted)

  # Arguments number differs from overridden method - pylint: disable=W0221
  def run(
      self, master_name, builder_name, build_number, good_revision,
      bad_revision, blame_list, try_job_type, compile_targets, targeted_tests):
    try_job_id = yield ScheduleTryJobPipeline(
        master_name, builder_name, build_number, good_revision, bad_revision,
        try_job_type, compile_targets, targeted_tests)
    try_job_result = yield MonitorTryJobPipeline(
        master_name, builder_name, build_number, try_job_type, try_job_id)
    yield IdentifyTryJobCulpritPipeline(
        master_name, builder_name, build_number, blame_list, try_job_type,
        try_job_id, try_job_result)
