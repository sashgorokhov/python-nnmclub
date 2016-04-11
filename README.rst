python-nnmclub
**************

Python library to search torrents on popular russian torrent tracker.

Installation
============

Via pip:

.. code-block:: shell

    pip install python-nnmclub

Usage
=====

.. code-block:: python

    import pynnmclub
    nnmclub = pynnmclub.NNMClub()
    results = nnmclub.search("Iron Man")

Return an iterable with dicts of all torrents found.

Torrent dict is:

.. code-block:: python

    {
        'topic',
        'detail_url',
        'download_url',
        'size',  # in bytes
        'seeders',
        'leechers',
        'added',  # type: datetime.datetime
        'views',
        'messages',
        'rating_number',  # how many people rated this,
        'rating',  # rating. float from 0 to 5
        'thanks',  # how many people thanked this torrent
    }

NOTE: With unathorized client you will be able to fetch only first 50 results of search.

Create an authorized client:

.. code-block:: python

    nnmclub = pynnmclub.NNMClub(username, password)

Or using previously created nnmclub client:

.. code-block:: python

    nnmclub.login(username, password)

If username or password are invalid, whis will raise an ``pynnmclub.InvalidCredentials`` error
(which is child to ``pynnmclub.NNMClubError``)

There is also a logger ``pynnmclub`` enabled that logs exceptions and warnings of parsing errors.
It also includes a full HTML of errored context as a DEBUG message.