from distutils.core import setup

with open('README.rst') as readme:
    with open('HISTORY.rst') as history:
        long_description = readme.read() + '\n\n' + history.read()

setup(
    requires=['beautifulsoup4', 'requests'],
    name='python-nnmclub',
    version='0.1',
    py_modules=['pynnmclub'],
    url='https://github.com/sashgorokhov/python-nnmclub',
    download_url='https://github.com/sashgorokhov/python-nnmclub/archive/master.zip',
    keywords=['nnm-club', 'nnmclub', 'torrent'],
    classifiers=[],
    long_description=long_description,
    license='MIT License',
    author='sashgorokhov',
    author_email='sashgorokhov@gmail.com',
    description='Python library to search torrents on popular russian torrent tracker.'
)