# coding=utf-8
import requests
import logging

import datetime

import re
from bs4 import BeautifulSoup

try:
    import urlparse
except ImportError:
    from urllib import parse as urlparse


logger = logging.getLogger('pynnmclub')

# logger.setLevel(logging.DEBUG)
# ch = logging.StreamHandler()
# ch.setLevel(logging.DEBUG)
# logger.addHandler(ch)

BASE_URL = 'http://nnmclub.to/'
FORUM_URL = urlparse.urljoin(BASE_URL, 'forum/')
LOGIN_URl = urlparse.urljoin(FORUM_URL, 'login.php')
SEARCH_URL = urlparse.urljoin(FORUM_URL, 'tracker.php')
TIMEOUT = 30.0

_result_dict_empty = {
    'topic': None,
    'detail_url': None,
    'download_url': None,
    'size': None,  # in bytes
    'seeders': None,
    'leechers': None,
    'added': None,  # type: datetime.datetime
    'views': None,
    'messages': None,
    'rating_number': None,  # how many people rated this,
    'rating': None,  # rating. float from 0 to 5
    'thanks': None,  # how many people thanked this torrent
    #'golden': None
}


_header_clean_map = {  # Header name -> callable returning cleaned data
    'Topic': lambda td: td.a.b.text,
    'Size': lambda td: int(td.u.text),
    'S': lambda td: int(td.b.text),
    'L': lambda td: int(td.b.text),
    'R': lambda td: int(td.text),
    'Added': lambda td: datetime.datetime.fromtimestamp(int(td.u.text)),
    'Th': lambda td: int(td.text) if '-' not in td.text else 0,
    'DL': lambda td: urlparse.urljoin(FORUM_URL, td.a['href'])
}


_header_to_result_map = { # Header name -> name in result dict
    'Topic': 'topic',
    'Size': 'size',
    'S': 'seeders',
    'L': 'leechers',
    'R': 'messages',
    'Added': 'added',
    'Th': 'thanks',
    'DL': 'download_url'
}


class NNMClubError(Exception): pass


class InvalidCredentials(NNMClubError): pass


class ParsingError(NNMClubError): pass


def _bs_from_response(response):
    """
    Returns BeautifulSoup from given requests response object.

    :param str|requests.Response response:
    :rtype: bs4.BeautifulSoup
    """
    if isinstance(response, requests.Response):
        response = response.text
    return BeautifulSoup(response, "html.parser")


def _bs_from_url(url):
    """
    Returns BeautifulSoup from given url.
    Shortcut function.

    :param str url:
    :rtype: bs4.BeautifulSoup
    """
    return _bs_from_response(requests.get(url))


class NNMClub:
    def __init__(self, username=None, password=None, session=None):
        """
        :param requests.Session session: optional requests.Session to use for creating requests.
        """
        self.username = username
        self.password = password
        self.session = session or requests.Session()
        self.session.params.update({'timeout': TIMEOUT})

        if self.username and self.password:
            self.login(self.username, self.password)

    def login(self, username, password):
        self.username = username
        self.password = password

        login_data = {'username': username, 'password': password, 'login': 'Вход'}
        response = self.session.post(LOGIN_URl, data=login_data)

        if self.username not in response.text:
            logger.warning('Invalid credentials: {0.username} {0.password}'.format(self))
            logger.debug(response.text)
            raise InvalidCredentials('Invalid credentials: username={0.username} password={0.password}'.format(self))

    def _get_table_headers(self, table):
        """
        :param bs4.element.Tag table:
        """
        ths = table.find_all('th')
        headers = list()
        for th in ths:
            text = th.text.strip()
            if text:
                headers.append(text)
        return headers

    def _row_map(self, headers, row):
        """
        :param list[str] headers:
        :param bs4.element.Tag row:
        :rtype: dict[str, bs4.element.Tag]
        """
        tds = row.find_all('td')[1:]
        return dict(zip(headers, tds))

    def _row_to_data(self, headers, row):
        """
        :param list[str] headers:
        :param bs4.element.Tag row:
        :rtype: dict
        """
        row_map = self._row_map(headers, row)
        result = _result_dict_empty.copy()

        for header_name, td in row_map.items():
            if header_name in _header_clean_map:
                try:
                    result[_header_to_result_map[header_name]] = _header_clean_map[header_name](td)
                except:
                    logger.warning('Error while parsing header %s', header_name, exc_info=True)
                    logger.debug(td)
                    continue

        if 'Rt' in row_map:
            td = row_map['Rt']
            rating_str = td.text.strip()
            match = re.search(r'(?P<rating>[\d\.]+)?.+?\((?P<rating_number>\d+)\)', rating_str)
            if match:
                rating = match.group('rating')
                rating = float(rating.replace(',', '.')) if rating else None
                rating_number = match.group('rating_number')
                rating_number = int(rating_number) if rating_number else None
            else:
                rating = None
                rating_number = None
            result['rating'] = rating
            result['rating_number'] = rating_number
        if 'Topic' in row_map:
            td = row_map['Topic']
            result['detail_url'] = urlparse.urljoin(FORUM_URL, td.a['href'])
            result['golden'] = td.find('Score') is not None
        if 'R' in row_map:
            td = row_map['R']
            result['views'] = int(re.match('(\d+)', td['title']).group())

        return result

    def _get_search_results(self, table):
        """
        :param bs4.element.Tag table:
        :rtype: collections.Iterable[dict]
        """
        rows = table.find_all('tr', attrs=['prow1', 'prow2'])
        headers = self._get_table_headers(table)

        for row in rows:
            try:
                yield self._row_to_data(headers, row)
            except Exception as e:
                logger.warning('Error while parsing row', exc_info=True)
                logger.debug(row)
                continue

    def search(self, text, max_pages=1):
        """
        :param str text:
        :param int|None max_pages: how many pages of results to parse. Default 1 - only first.
        :rtype: collections.Iterable[dict]
        """
        pages_parsed = 0

        search_data = {'nm': text, 'shr': 1, 'sht': 1}  # shr shows rating column; sht shows thanks column

        response = self.session.post(SEARCH_URL, data=search_data)

        while max_pages is None or (max_pages and pages_parsed < max_pages):
            pages_parsed += 1

            bs = _bs_from_response(response)
            try:
                table = bs.find(attrs='forumline tablesorter')
                if not table:
                    raise ParsingError('Table (forumline tablesorter) not found')

                for result in self._get_search_results(bs):
                    yield result

                try:
                    next_table = list(table.next_siblings)[1]
                    span = next_table.find_all('td')[1].span
                    links = span.find_all('a')
                    if len(links) > 0:
                        if 'След.' in links[-1].text:
                            url = urlparse.urljoin(FORUM_URL, links[-1]['href'])
                            response = self.session.get(url)
                        else:
                            break
                    else:
                        break
                except Exception as e:
                    raise ParsingError(str(e))
            except ParsingError:
                logger.exception('Error while parsing results on page %s of "%s"', pages_parsed, text)
                logger.debug(response.text)
                raise