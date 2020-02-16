#!/usr/bin/env python3

import pytest
import os
import nagiosplugin

import check_gitlab_pipelines


class TestGitlab:

    json_files = [
        ('projects', 'mockdata/projects.json'),
        ('projects/1/pipelines', 'mockdata/pipelines_p1.json'),
        ('projects/5/pipelines', 'mockdata/pipelines_p5.json'),
    ]

    projects = [
        (
            {'id': 5, 'name': 'groupapp', 'path_with_namespace': 'group/groupapp'},
            {'status': 'failed', 'status_code': 2, 'pipeline_id': '246'}
        ),
        (
            {'id': 1, 'name': 'groupapi', 'path_with_namespace': 'group/groupapi'},
            {'status': 'success', 'status_code': 0, 'pipeline_id': '303'}
        )

    ]

    def __mock_all(self, m):
        """ load data """
        dir_path = os.path.dirname(os.path.realpath(__file__))
        for url, file_path in TestGitlab.json_files:
            with open('{0}/{1}'.format(dir_path, file_path), 'r') as file:

                m.register_uri(
                    'GET',
                    'http://localhost/api/v4/' + url,
                    text=file.read()
                )

    def test_projects(self, requests_mock):

        self.__mock_all(requests_mock)
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

        self.__mock_all(requests_mock)
        gitlab = check_gitlab_pipelines.Gitlab('http://localhost', '')

        for project, result in TestGitlab.projects:
            status = gitlab.get_pipelines_status(project, [], ['master'])

            for key in ['status', 'status_code']:
                assert status[key] == result[key]

            assert 'https://gitlab.localhost.localdomain/{0}/pipelines/{1}'.format(
                project['path_with_namespace'], result['pipeline_id']
            ) in status['web_url']

    def test_pipeline_warning(self, requests_mock):

        self.__mock_all(requests_mock)
        gitlab = check_gitlab_pipelines.Gitlab('http://localhost', '')
        project, res = TestGitlab.projects[0]

        # get project and warn for master failure
        res = gitlab.get_pipelines_status(project, ['master'], [])

        assert res['status_code'] == 1

    def test_pipeline_warning_overlapping(self, requests_mock):

        self.__mock_all(requests_mock)
        gitlab = check_gitlab_pipelines.Gitlab('http://localhost', '')
        project, res = TestGitlab.projects[0]

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
