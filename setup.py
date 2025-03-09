from setuptools import setup

setup(
    name='docugen',
    license='MIT',
    version='0.0.1',
    description='A powerful Python documentation generator that swoops in to automatically create and maintain clean, comprehensive docstrings for your codebase',
    entry_points={
        'console_scripts': [
            'docugen = docugen.cli:main',
        ],
        'pre-commit': [
            'docugen = docugen.cli:main',
        ],
    },
)
