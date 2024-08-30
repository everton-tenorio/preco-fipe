import requests


def req(url, data):
        return requests.post(url, data=data).json()