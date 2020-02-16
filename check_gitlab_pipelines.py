#!/usr/bin/env python3

"""checks gitlab pipeline status"""

import nagiosplugin
import argparse
import requests
import re

from datetime import datetime


class Gitlab:

    strptime_format = '%Y-%m-%dT%H:%M:%S.%fZ'
    not_completed_status = [
        'running',
        'pending',
        'canceled',
        'skipped'
    ]

    def __init__(self, url, token):

        self.url = url + '/api/v4'
        self.token = token

        self.http_response_messages = {
            401: 'pat {0}... rejected'.format(self.token[:3]),
            404: 'gitlab instance not found'
        }

    def get_projects(self):

        request_keys = [
            'id',
            'name',
            'path_with_namespace'
        ]
        projects = []

        response = self.__request('/projects')

        for project in response:
            obj = {}
            for key in request_keys:
                obj[key] = project[key]
            projects.append(obj)

        return projects

    def get_pipelines_status(self, project, warning_refs, critical_refs):

        ret_obj = {}
        response = self.__request('/projects/{0}/pipelines'.format(project['id']))

        least_pipeline = {}
        most_significant_code = 0
        for pipeline_status in response:
            ref = pipeline_status['ref']
            status = pipeline_status['status']
            updated_at = datetime.strptime(pipeline_status['updated_at'], Gitlab.strptime_format)

            """ shortcut if ref is not monitored or is not completed or newer pipeline found"""
            if (ref not in critical_refs and ref not in warning_refs) or \
                    status in Gitlab.not_completed_status or \
                    (ref in least_pipeline and least_pipeline[ref] > updated_at):
                continue

            """ this is the pipeline we want, determine status """
            status_code = 0
            if status == 'failed':
                if ref in critical_refs:  # critical wins
                    status_code = 2
                elif ref in warning_refs:
                    status_code = 1

            """ highest failure code wins"""
            if status_code not in ret_obj or status_code > most_significant_code:
                ret_obj = {
                    'metric_name': project['path_with_namespace'],
                    'web_url': pipeline_status['web_url'],
                    'status': status,
                    'status_code': status_code,
                    'ref': ref
                }
                least_pipeline[ref] = updated_at
                most_significant_code = status_code

        return ret_obj

    def __request(self, url):

        login_header = {}
        if len(self.token) != 0:
            login_header['Private-Token'] = self.token

        try:
            response = requests.get(
                self.url + url,
                headers=login_header
            )
        except requests.exceptions.ConnectionError:
            raise nagiosplugin.CheckError('connection to {0} failed'.format(self.url))

        if response.status_code != 200:
            raise nagiosplugin.CheckError(
                self.http_response_messages.get(
                    response.status_code, 'unknown failure'
                )
            )

        return response.json()


class Pipelines(nagiosplugin.Resource):

    def __init__(self, args):
        self.args = args
        self.gitlab = Gitlab(args.url, args.token)

        """ unpack argparse warning and critical refs """
        self.warn = []
        self.crit = []
        for el in self.args.warningref:
            self.warn.append(el[0])
        for el in self.args.criticalref:
            self.crit.append(el[0])

        if len(self.warn) == 0 and len(self.crit) == 0:
            self.crit = ['master']  # set default

    def probe(self):

        for project in self.gitlab.get_projects():

            if not self.__check_name(project):
                continue

            status = self.gitlab.get_pipelines_status(
                project,
                self.warn,
                self.crit,
            )
            yield nagiosplugin.Metric(
                status['metric_name'],
                status['status_code'],
                context='pipeline_status'
            )

    def __check_name(self, project):

        if len(self.args.project) == 0:
            return True

        for element in self.args.project:
            re_string = element[0]
            pattern = re.compile(re_string)
            if pattern.match(project['path_with_namespace']):
                return True
        return False


class GitlabSummary(nagiosplugin.Summary):

    def ok(self, results):
        return ''

    def problem(self, results):

        string = ''
        for ix in results:
            if ix.metric.value > 0:
                if len(string) != 0:
                    string = string + ' '
                string = string + '{0} failed'.format(ix.metric.name)

        return string


@nagiosplugin.guarded
def main():
    """
    parse args
    """
    argp = argparse.ArgumentParser(description=__doc__)
    argp.add_argument(
        '-u', '--url',
        metavar='url', default='http://localhost', type=str,
        help='url of gitlab server api, defaults to http://localhost'
    )
    argp.add_argument(
        '-t', '--token',
        metavar='token', default='', type=str,
        help='gitlab pat'
    )
    argp.add_argument(
        '-p', '--project',
        metavar='project regex', nargs='+', action='append', type=str, default=[],
        help='project name regexes, can be used multiple times'
    )
    argp.add_argument(
        '-w', '--warningref',
        metavar='warning refs', nargs='+', action='append', type=str, default=[],
        help='refs that generate a warning if the last state is failed'
    )
    argp.add_argument(
        '-c', '--criticalref',
        metavar='critical refs', nargs='+', action='append', type=str, default=[],
        help='critical refs'
    )
    argp.add_argument('-v', '--verbose', action='count', default=0)

    args = argp.parse_args()

    """
    start checks
    """
    check = nagiosplugin.Check(
        Pipelines(args),
        nagiosplugin.ScalarContext('pipeline_status', '0:0', '0:1'),
        GitlabSummary()
    )
    check.main(args.verbose)


if __name__ == '__main__':
    main()
