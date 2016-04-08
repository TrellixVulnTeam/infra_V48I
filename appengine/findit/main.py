# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import endpoints
import webapp2

from findit_api import FindItApi
from handlers import build_failure
from handlers import check_duplicate_failures
from handlers import config
from handlers import failure_log
from handlers import help_triage
from handlers import list_analyses
from handlers import monitor_alerts
from handlers import swarming_task
from handlers import triage_analysis
from handlers import trigger_analyses
from handlers import try_job
from handlers import try_job_result
from handlers import verify_analysis
from handlers import version
from pipeline_wrapper import pipeline_status_ui


# This is for the default module.
default_web_pages_handler_mappings = [
    ('/version', version.Version),
]
default_web_application = webapp2.WSGIApplication(
    default_web_pages_handler_mappings, debug=False)


# This is for Cloud Endpoint apis in the default module.
api_application = endpoints.api_server([FindItApi])


# This is for appengine pipeline status pages in the default module.
pipeline_status_handler_mappings = [
    ('/_ah/pipeline/rpc/tree', pipeline_status_ui._TreeStatusHandler),
    ('/_ah/pipeline/rpc/class_paths', pipeline_status_ui._ClassPathListHandler),
    ('/_ah/pipeline/rpc/list', pipeline_status_ui._RootListHandler),
    ('/_ah/pipeline(/.+)', pipeline_status_ui._StatusUiHandler),
]
pipeline_status_application = webapp2.WSGIApplication(
    pipeline_status_handler_mappings, debug=False)


# This is for the "waterfall-frontend" module.
waterfall_frontend_web_pages_handler_mappings = [
    ('/build-failure', build_failure.BuildFailure),
    ('/list-analyses', list_analyses.ListAnalyses),
    ('/waterfall/build-failure', build_failure.BuildFailure),
    ('/waterfall/check-duplicate-failures',
     check_duplicate_failures.CheckDuplicateFailures),
    ('/waterfall/config', config.Configuration),
    ('/waterfall/failure-log', failure_log.FailureLog),
    ('/waterfall/help-triage', help_triage.HelpTriage),
    ('/waterfall/list-analyses', list_analyses.ListAnalyses),
    ('/waterfall/monitor-alerts', monitor_alerts.MonitorAlerts),
    ('/waterfall/swarming-task', swarming_task.SwarmingTask),
    ('/waterfall/triage-analysis', triage_analysis.TriageAnalysis),
    ('/waterfall/try-job', try_job.TryJob),
    ('/waterfall/try-job-result', try_job_result.TryJobResult),
    ('/waterfall/verify-analysis', verify_analysis.VerifyAnalysis),
]
waterfall_frontend_web_application = webapp2.WSGIApplication(
    waterfall_frontend_web_pages_handler_mappings, debug=False)


# This is for the "waterfall-backend" module.
waterfall_backend_web_pages_handler_mappings = [
    ('/waterfall/trigger-analyses', trigger_analyses.TriggerAnalyses),
]
waterfall_backend_web_application = webapp2.WSGIApplication(
    waterfall_backend_web_pages_handler_mappings, debug=False)
