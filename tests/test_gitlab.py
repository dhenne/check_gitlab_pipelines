#!/usr/bin/env python3

import pytest
import nagiosplugin
import check_gitlab_pipelines
from . import mock as Mock


class TestGitlab:

    def test_projects(self, requests_mock):

        Mock.Data.mock_all(requests_mock)
        gitlab = check_gitlab_pipelines.Gitlab('http://localhost', '')

        projects = gitlab.get_projects()

        assert len(projects) == 2

        for ix, suffix in enumerate(['app', 'api']):
            for key in ['id', 'name', 'path_with_namespace']:
                assert key in projects[ix]

            assert isinstance(projects[ix]['id'], int)
            assert projects[ix]['name'] == 'group' + suffix
            assert projects[ix]['path_with_namespace'] == 'group/group' + suffix

    def test_pipelines(self, requests_mock):

        Mock.Data.mock_all(requests_mock)
        gitlab = check_gitlab_pipelines.Gitlab('http://localhost', '')

        for project, result in Mock.Data.projects:
            status = gitlab.get_pipelines_status(project, [], ['master'])

            for key in ['status', 'status_code']:
                assert status[key] == result[key]

            assert 'https://gitlab.localhost.localdomain/{0}/pipelines/{1}'.format(
                project['path_with_namespace'], result['pipeline_id']
            ) in status['web_url']

    def test_pipeline_warning(self, requests_mock):

        Mock.Data.mock_all(requests_mock)
        gitlab = check_gitlab_pipelines.Gitlab('http://localhost', '')
        project, res = Mock.Data.projects[0]

        # get project and warn for master failure
        res = gitlab.get_pipelines_status(project, ['master'], [])

        assert res['status_code'] == 1

    def test_pipeline_warning_overlapping(self, requests_mock):

        Mock.Data.mock_all(requests_mock)
        gitlab = check_gitlab_pipelines.Gitlab('http://localhost', '')
        project, res = Mock.Data.projects[0]

        res = gitlab.get_pipelines_status(project, ['master'], ['master'])

        assert res['status_code'] == 2

    def test_unauthenticated(self, requests_mock):

        requests_mock.register_uri(
                    'GET',
                    'http://localhost/api/v4/projects',
                    text='not authenticated', status_code='401'
                )

        gitlab = check_gitlab_pipelines.Gitlab('http://localhost', '')

        with pytest.raises(nagiosplugin.CheckError):
            gitlab.get_projects()

    def test_notfound(self, requests_mock):

        requests_mock.register_uri(
                    'GET',
                    'http://localhost/api/v4/projects',
                    text='not authenticated', status_code='404'
                )

        gitlab = check_gitlab_pipelines.Gitlab('http://localhost', '')

        with pytest.raises(nagiosplugin.CheckError):
            gitlab.get_projects()

    def test_regex(self, requests_mock):

        Mock.Data.mock_all(requests_mock)
        gitlab = check_gitlab_pipelines.Gitlab('http://localhost', '')


