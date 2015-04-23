from setuptools import setup, find_packages
import os.path as p


version = "0.2.3"

with open(p.join(p.dirname(__file__), 'requirements', 'package.txt'), 'r') as reqs:
    install_requires = [line.strip() for line in reqs]

tests_require = []
try:
    with open(p.join(p.dirname(__file__), 'requirements', 'test.txt'), 'r') as reqs:
        tests_require = [line.strip() for line in reqs]
except IOError:
    pass

setup(
    name="twitterbot",
    version=version,
    author="Jessamyn Smith",
    author_email="jessamyn.smith@gmail.com",
    url="https://github.com/jessamynsmith/twitterbot",
    download_url='https://github.com/jessamynsmith/twitterbot/archive/v{0}.tar.gz'.format(version),
    license='MIT',
    description="Configurable bot that replies to mentions and posts messages to twitter",
    long_description=open('README.rst').read(),
    keywords=['twitter', 'bot', 'web 2.0', 'command-line tools'],

    install_requires=install_requires,
    tests_require=tests_require,

    packages=find_packages(exclude=['*test*']),

    # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'License :: OSI Approved :: MIT License',
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content :: CGI Tools/Libraries",
        "Topic :: Software Development",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
    ])
