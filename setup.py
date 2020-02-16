from setuptools import setup

setup(
    name='check_gitlab_pipelines',
    version='0.1',
    description='Nagios check for gitlab pipelines',
    url='http://github.com/aufbaubank/check_gitlab_pipelines',
    author='Daniel Henneberg',
    author_email='daniel.henneberg@aufbaubank.de',
    license='MIT',
    scripts=['check_gitlab_pipelines.py'],
    zip_safe=False
)