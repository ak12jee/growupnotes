#!/usr/bin/python
# -*- coding: UTF-8 -*-

import hashlib
import requests


class HttpClient(object):
    @staticmethod
    def format_str(params, symbol, join_str):
        src_str = join_str.join(
            k + symbol + str(params[k]) for k in sorted(params.keys()))
        return src_str

    @staticmethod
    def signature(params, method, url, data=None):
        data_str = ""
        headers_str = HttpClient.format_str(params=params, symbol=":", join_str="")
        if data is not None:
            data_str = "?" + HttpClient.format_str(params=data, symbol="=", join_str="&")
        sign_str = str(method).upper() + headers_str + url + data_str + "3c6e0b8a9c15224a8228b9a98ca1531d"
        return HttpClient.md5(sign_str)

    @staticmethod
    def md5(sign_str):
        hash_md5 = hashlib.md5()
        hash_md5.update(str(sign_str).encode("utf-8"))
        sign_md5 = hash_md5.hexdigest()
        return sign_md5

    @staticmethod
    def get_sign(headers, method, url, params=None):
        sign_headers = dict()
        sign_headers["X-QP-AppId"] = headers["X-QP-AppId"]
        sign_headers["X-QP-Timestamp"] = headers["X-QP-Timestamp"]
        sign_headers["X-QP-Nonce"] = headers["X-QP-Nonce"]
        headers["X-QP-Signature"] = str(HttpClient.signature(method=str(method).upper(), url=url, params=sign_headers, data=params)).upper()
        return headers

    @staticmethod
    def get(headers, params, url):
        if len(headers) != 0:
            headers = HttpClient.get_sign(headers=headers, params=params, url=url, method="get")
        try:
            res = requests.get(url=url, params=params, headers=headers)
            return res.json()
        except Exception as e:
            print str(e)
            return None

    @staticmethod
    def post(headers, params, url):
        headers = HttpClient.get_sign(headers=headers, url=url, method="post")
        try:
            res = requests.post(url=url, json=params, headers=headers)
            return res.json()
        except Exception as e:
            print str(e)
            return None

    @staticmethod
    def patch(headers, params, url):
        headers = HttpClient.get_sign(headers=headers, url=url, method="patch")
        try:
            res = requests.patch(url=url, json=params, headers=headers)
            return res.json()
        except Exception as e:
            print str(e)
            return None
