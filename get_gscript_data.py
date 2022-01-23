import requests
import json


class GetGScriptData:
    def __init__(self, url):
        self.url = url

    def getConfig(self):
        assert self.url != "", 'url is invalid'
        payload = {'type': 'config'}
        res = requests.get(url=self.url, params=payload)
        jsonstr = json.loads(res.text)
        if jsonstr["status"]:
            return jsonstr["result"]["username"], \
                   jsonstr["result"]["password"], \
                   jsonstr["result"]["delay"]

        else:
            assert False, 'error: ' + jsonstr["message"]

    def getEnabled(self, qnaire_id):
        assert self.url != "", 'url is invalid'
        payload = {'type': 'enabled'}
        res = requests.get(url=self.url, params=payload)
        jsonstr = json.loads(res.text)
        if jsonstr["status"]:
            for key in jsonstr["result"]:
                if key == qnaire_id:
                    return jsonstr["result"].get(key)
        else:
            assert False, 'error: ' + jsonstr["message"]
        return False

    def getRecentLog(self, count):
        assert self.url != "", 'url is invalid'
        payload = {'type': 'log', 'count': count}
        res = requests.get(url=self.url, params=payload)
        jsonstr = json.loads(res.text)
        if jsonstr["status"]:
            return jsonstr["result"]
        else:
            assert False, 'error: ' + jsonstr["message"]

    def getHolidaybool(self):
        assert self.url != "", 'url is invalid'
        payload = {'type': 'holidaybool'}
        res = requests.get(url=self.url, params=payload)
        jsonstr = json.loads(res.text)
        if jsonstr["status"]:
            return jsonstr["result"]
        else:
            assert False, 'error: ' + jsonstr["message"]

    def getTasks(self):
        assert self.url != "", 'url is invalid'
        payload = {'type': 'task'}
        res = requests.get(url=self.url, params=payload)
        jsonstr = json.loads(res.text)
        tasks = ""
        if jsonstr["status"]:
            for data in jsonstr["result"]:
                tasks += data + '\n'
            return tasks

        else:
            assert False, 'error: ' + jsonstr["message"]

    def getKeywords3949(self):
        assert self.url != "", 'url is invalid'
        payload = {'type': 'keywords3949'}
        res = requests.get(url=self.url, params=payload)
        jsonstr = json.loads(res.text)
        if jsonstr["status"]:
            return jsonstr["result"]
        else:
            assert False, 'error: ' + jsonstr["message"]

    def writeLog(self, qnaireId, status, message):
        assert self.url != "", 'url is invalid'
        data = {"type": "log", "data": {"qnaireId": qnaireId, "status": status, "message": message}}
        res = requests.post(url=self.url, json=data)
        jsonstr = json.loads(res.text)
        if not jsonstr["status"]:
            assert False, 'error: ' + jsonstr["message"]

