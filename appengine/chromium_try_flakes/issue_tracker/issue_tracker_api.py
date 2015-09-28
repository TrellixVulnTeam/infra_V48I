"""Provides API wrapper for the codesite issue tracker"""

import httplib2
import logging
import time

from apiclient import discovery
from apiclient.errors import HttpError
from issue_tracker.issue import Issue
from issue_tracker.comment import Comment
from oauth2client.appengine import AppAssertionCredentials


# The scope needed for the credentials to access the projecthosting api.
PROJECT_HOSTING_SCOPE = 'https://www.googleapis.com/auth/projecthosting'


# TODO(akuegel): Do we want to use a different timeout? Do we want to use a
# cache? See documentation here:
# https://github.com/jcgregorio/httplib2/blob/master/python2/httplib2/__init__.py#L1142
def _createHttpObject(scope):
  credentials = AppAssertionCredentials(scope=scope)
  return credentials.authorize(httplib2.Http())


def _buildClient(api_name, api_version, http, discovery_url):
  # This occassionally hits a 503 "Backend Error". Hopefully a simple retry
  # can recover.
  tries_left = 5
  tries_wait = 10
  while tries_left:
    tries_left -= 1
    try:
      client = discovery.build(
          api_name, api_version,
          discoveryServiceUrl=discovery_url,
          http=http)
      break
    except HttpError as e:
      if tries_left:
        logging.error(
            'apiclient.discovery.build() failed for %s: %s', api_name, e)
        logging.error(
            'Retrying apiclient.discovery.build() in %s seconds.', tries_wait)
        time.sleep(tries_wait)
      else:
        logging.exception(
            'apiclient.discovery.build() failed for %s too many times.',
            api_name)
        raise e
  return client


class IssueTrackerAPI(object):
  CAN_ALL = 'all'

  """A wrapper around the issue tracker api."""
  def __init__(self, project_name):
    self.project_name = project_name
    discovery_url = ('https://www.googleapis.com/discovery/v1/apis/{api}/'
                     '{apiVersion}/rest')
    self.client = _buildClient('projecthosting', 'v2',
                               _createHttpObject(PROJECT_HOSTING_SCOPE),
                               discovery_url)


  def create(self, issue, send_email=True):
    cc = [{'name': user} for user in issue.cc]
    tmp = self.client.issues().insert(projectId=self.project_name,
                                      sendEmail=send_email,
                                      body={'summary': issue.summary,
                                            'description': issue.description,
                                            'status': issue.status,
                                            'owner': {'name': issue.owner},
                                            'labels': issue.labels,
                                            'cc': cc}).execute()
    issue.id = int(tmp['id'])
    issue.dirty = False
    return issue

  def update(self, issue, comment=None, send_email=True):
    if not issue.dirty and not comment:
      return issue
    if not issue.owner:
      # workaround for existing bug:
      # https://code.google.com/a/google.com/p/codesite/issues/detail?id=115
      issue.owner = '----'

    updates = {}
    if 'summary' in issue.changed:
      updates['summary'] = issue.summary
    if 'status' in issue.changed:
      updates['status'] = issue.status
    if 'owner' in issue.changed:
      updates['owner'] = issue.owner
    if 'blocked_on' in issue.changed:
      updates['blockedOn'] = issue.blocked_on
    if issue.labels.isChanged():
      updates['labels'] = list(issue.labels.added)
    if issue.cc.isChanged():
      # TODO: figure out what this logic should be, I have yet to make this work
      # Probably doesn't work if update involves removals.
      updates['cc'] = list(issue.cc.added)

    body = {'id': issue.id,
            'updates': updates}

    if comment:
      body['content'] = comment

    self.client.issues().comments().insert(projectId=self.project_name,
                                           issueId=issue.id,
                                           sendEmail=send_email,
                                           body=body).execute()

    if issue.owner == '----':
      issue.owner = ''

    issue.dirty = False
    return issue

  def addComment(self, issue_id, comment, send_email=True):
    issue = self.getIssue(issue_id)
    self.update(issue, comment, send_email)

  def getCommentCount(self, issue_id):
    feed = self.client.issues().comments().list(projectId=self.project_name,
                                                issueId=issue_id,
                                                startIndex=1,
                                                maxResults=0).execute()
    return feed.get('totalResults', '0')

  def getComments(self, issue_id):
    rtn = []

    feed = self.client.issues().comments().list(projectId=self.project_name,
                                                issueId=issue_id).execute()
    rtn.extend([Comment(entry) for entry in feed['items']])
    total_results = feed['totalResults']
    if not total_results:
      return rtn

    while len(rtn) < total_results:
      feed = self.client.issues().comments().list(projectId=self.project_name,
                                                  issueId=issue_id,
                                                  startIndex=len(rtn)).execute()
      rtn.extend([Comment(entry) for entry in feed['items']])

    return rtn

  def getFirstComment(self, issue_id):
    feed = self.client.issues().comments().list(projectId=self.project_name,
                                                issueId=issue_id,
                                                startIndex=0,
                                                maxResults=1).execute()
    if 'items' in feed and len(feed['items']) > 0:
      return Comment(feed['items'][0])
    return None

  def getLastComment(self, issue_id):
    total_results = self.getCommentCount(issue_id)
    feed = self.client.issues().comments().list(projectId=self.project_name,
                                                issueId=issue_id,
                                                startIndex=total_results-1,
                                                maxResults=1).execute()
    if 'items' in feed and len(feed['items']) > 0:
      return Comment(feed['items'][0])
    return None

  def getIssue(self, issue_id):
    """Retrieve a set of issues in a project."""
    entry = self.client.issues().get(projectId=self.project_name,
                                     issueId=issue_id).execute()
    return Issue(entry)