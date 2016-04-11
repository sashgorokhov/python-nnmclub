import requests
import unittest
import pynnmclub


class TestPyNnmClub(unittest.TestCase):
    text = 'Iron Man'

    def setUp(self):
        self.client = pynnmclub.NNMClub()

    def test_base_url_reachable(self):
        resp = requests.head(pynnmclub.BASE_URL)
        resp.raise_for_status()

    def test_search(self):
        iterable = self.client.search(self.text)
        result_list = list(iterable)

        self.assertGreater(len(result_list), 0)