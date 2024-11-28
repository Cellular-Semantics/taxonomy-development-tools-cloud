from setuptools import setup, find_packages

setup(
    name='tdt_api',
    version='0.0.0',
    description='Taxonomy Development Tools restful API.',
    url='https://github.com/Cellular-Semantics/taxonomy-development-tools-cloud',
    author='Huseyin Kir',

    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Brain Data Standards Ontology',
        'License :: Apache License Version 2.0',
        'Programming Language :: Python :: 3.6',
    ],

    keywords='rest flask swagger flask-restplus tdt',

    packages=find_packages(),

    install_requires=['flask==2.1.2', 'flask-restx>=0.5.1', 'werkzeug==2.0.2'],
)