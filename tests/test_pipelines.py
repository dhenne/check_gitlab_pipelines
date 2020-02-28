#!/usr/bin/env python3

import nagiosplugin
import check_gitlab_pipelines
from . import mock as Mock
import re


class TestPipelines:

    simple_regexes = [
        '.*api',
        '.*app'
    ]

    @staticmethod
    def __pipelines_by_args(args_ary):

        args = check_gitlab_pipelines.create_argparser(args_ary)
        return check_gitlab_pipelines.Pipelines(args)

    def test_regex(self, requests_mock):

        Mock.Data.mock_all(requests_mock)

        for regex in TestPipelines.simple_regexes:

            result = self.__pipelines_by_args(['-p', regex]).probe()

            for ix in result:
                assert isinstance(ix, nagiosplugin.Metric)
                assert re.compile(regex).match(ix.name)

    def test_regexes_all_at_once(self, requests_mock):

        Mock.Data.mock_all(requests_mock)

        args_ary = []
        for ix in TestPipelines.simple_regexes:
            args_ary.append('-p')
            args_ary.append(ix)

        results = list(
            self.__pipelines_by_args(args_ary).probe()
        )

        assert len(results) == 2






