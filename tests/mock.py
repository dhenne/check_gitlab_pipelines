import os

class Data:

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

    @staticmethod
    def mock_all(m):
        """ load data """
        dir_path = os.path.dirname(os.path.realpath(__file__))
        for url, file_path in Data.json_files:
            with open('{0}/{1}'.format(dir_path, file_path), 'r') as file:

                m.register_uri(
                    'GET',
                    'http://localhost/api/v4/' + url,
                    text=file.read()
                )