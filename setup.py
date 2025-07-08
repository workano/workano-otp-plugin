#!/usr/bin/env python3

from setuptools import find_packages
from setuptools import setup

setup(
    name='workano-otp-plugin',
    version='1.0',
    description='workano otp request plugin',
    author='workano team',
    author_email='info@workano.com',
    packages=find_packages(),
    url='https://workano.com',
    include_package_data=True,
    package_data={
        'workano_otp_plugin': ['api.yml'],
    },

    entry_points={
        'wazo_calld.plugins': [
            'workano_otp_plugin = workano_otp_plugin.plugin:Plugin'
        ]
    }
)
