#!/usr/bin/env python3

import pytest
import os
import nagiosplugin

import check_gitlab_pipelines


class TestGitlab:

    def test_brokenjson(self, requests_mock):

        requests_mock.register_uri(
            'GET',
            'http://localhost/api/v4/projects',
            text='not authenticated', status_code='404'
        )

        gitlab = check_gitlab_pipelines.Gitlab('http://localhost', '')

        with pytest.raises(nagiosplugin.CheckError):
            gitlab.get_projects()
