import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(BASE_DIR))
sys.path.insert(0, os.path.join(BASE_DIR, 'common'))

import unittest
import json

from csdn import create_app
from settings.testting import TestingConfig


class SearchTest(unittest.TestCase):
    def setUp(self) -> None:
        flask_app = create_app(TestingConfig)
        self.test_client = flask_app.test_client()

    def test_normal_request(self):
        resp = self.test_client.get("/v1/search/suggest?keyword=pyhton")
        self.assertEqual(resp.status_code,200)
        resp_json = resp.data
        resp_dict = json.loads(resp_json)

        self.assertIn('message', resp_dict)
        self.assertIn('data', resp_dict)
        data = resp_dict['data']
        self.assertIn('options', data)

    def test_missing_request_param_q(self):
        """
        测试接口请求时缺少参数q的场景
        :return:
        """
        resp = self.test_client.get('/v1/search/suggest')
        self.assertEqual(resp.status_code, 400)  # 响应状态码

    def test_request_param_q_length_error(self):
        """
        测试接口请求时q参数超过长度限制
        :return:
        """
        resp = self.test_client.get('/v1/search/suggest?keyword=' + 'e' * 51)
        self.assertEqual(resp.status_code, 400)  # 响应状态码

if __name__ == "__main__":
    unittest.main()