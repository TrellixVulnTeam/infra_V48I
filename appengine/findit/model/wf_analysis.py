# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from google.appengine.ext import ndb

from model.base_build_model import BaseBuildModel
from model import analysis_status
from model import result_status


class WfAnalysis(BaseBuildModel):
  """Represents an analysis of a build of a builder in a Chromium waterfall.

  'Wf' is short for waterfall.
  """
  @staticmethod
  def _CreateKey(master_name, builder_name, build_number):  # pragma: no cover
    return ndb.Key('WfAnalysis',
                   BaseBuildModel.CreateBuildId(
                       master_name, builder_name, build_number))

  @staticmethod
  def Create(master_name, builder_name, build_number):  # pragma: no cover
    return WfAnalysis(
        key=WfAnalysis._CreateKey(master_name, builder_name, build_number))

  @staticmethod
  def Get(master_name, builder_name, build_number):  # pragma: no cover
    return WfAnalysis._CreateKey(master_name, builder_name, build_number).get()

  @property
  def completed(self):
    return self.status in (
        analysis_status.COMPLETED, analysis_status.ERROR)

  @property
  def duration(self):
    if not self.completed or not self.end_time or not self.start_time:
      return None

    return int((self.end_time - self.start_time).total_seconds())

  @property
  def failed(self):
    return self.status == analysis_status.ERROR

  @property
  def status_description(self):
    return analysis_status.STATUS_TO_DESCRIPTION.get(self.status, 'Unknown')

  @property
  def result_status_description(self):
    return result_status.RESULT_STATUS_TO_DESCRIPTION.get(
        self.result_status, '')

  @property
  def correct(self):
    """Returns whether the analysis result is correct or not.

    Returns:
      True: correct
      False: incorrect
      None: don't know yet.
    """
    if not self.completed or self.failed:
      return None

    if self.result_status in (
        result_status.FOUND_CORRECT,
        result_status.NOT_FOUND_CORRECT,
        result_status.FOUND_CORRECT_DUPLICATE):
      return True

    if self.result_status in (
        result_status.FOUND_INCORRECT,
        result_status.NOT_FOUND_INCORRECT,
        result_status.FOUND_INCORRECT_DUPLICATE):
      return False

    return None

  def Reset(self):  # pragma: no cover
    """Resets to the state as if no analysis is run."""
    self.pipeline_status_path = None
    self.status = analysis_status.PENDING
    self.request_time = None
    self.start_time = None
    self.end_time = None

  # When the build cycle started.
  build_start_time = ndb.DateTimeProperty(indexed=True)
  build_completed = ndb.BooleanProperty(indexed=False)

  # The url path to the pipeline status page.
  pipeline_status_path = ndb.StringProperty(indexed=False)
  # The status of the analysis.
  status = ndb.IntegerProperty(
      default=analysis_status.PENDING, indexed=False)
  # When the analysis was requested.
  request_time = ndb.DateTimeProperty(indexed=False)
  # When the analysis actually started.
  start_time = ndb.DateTimeProperty(indexed=False)
  # When the analysis actually ended.
  end_time = ndb.DateTimeProperty(indexed=False)
  # When the analysis was updated.
  updated_time = ndb.DateTimeProperty(indexed=False, auto_now=True)
  # Record which version of analysis.
  version = ndb.StringProperty(indexed=False)

  # Analysis result for the build failure.
  not_passed_steps = ndb.StringProperty(indexed=False, repeated=True)
  result = ndb.JsonProperty(indexed=False, compressed=True)
  # Suspected CLs we found.
  suspected_cls = ndb.JsonProperty(indexed=False, compressed=True)
  # Record the id of try job results of each failure.
  failure_result_map = ndb.JsonProperty(indexed=False, compressed=True)

  # The actual culprit CLs that are responsible for the failures.
  culprit_cls = ndb.JsonProperty(indexed=False, compressed=True)
  # Conclusion of analysis result for the build failure: 'Found' or 'Not Found'.
  result_status = ndb.IntegerProperty(indexed=True)
  # Record the history of triage.
  triage_history = ndb.JsonProperty(indexed=False, compressed=True)
