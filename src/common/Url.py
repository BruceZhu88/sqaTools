
import requests
from urllib import request


def request_url(url, data=None, timeout=None):
    status = ""
    try:
        req = request.Request(url, data)
        if timeout is not None:
            res = request.urlopen(req, timeout=timeout)
        else:
            res = request.urlopen(req)
        status = res.status
        # data = urllib.request.urlopen(url, timeout=8)
        text = res.read().decode('utf-8')
    except Exception as e:
        text = "error"
    return {"content": text, "status": status}


def requests_url(url, mode, data=None, timeout=5):
    r = None
    try:
        if mode == 'get':
            r = requests.get(url, data=data, timeout=timeout)
        elif mode == 'post':
            r = requests.post(url, data=data, timeout=timeout)
        elif mode == 'put':
            r = requests.put(url, data=data, timeout=timeout)
        content, status_code = r.content.decode('utf-8'), r.status_code
    except Exception as e:
        content, status_code = 'error', ''
    return {'content': content, 'status': status_code}


def check_url_status(url, timeout=20.0):
    try:
        req = request.Request(url)
        response = request.urlopen(req, timeout=timeout)
        # status = response.status
        return True
        # except URLError as e:
    except Exception as e:
        # self.log.debug("Cannot connect {}: {}".format(url, e))
        return False


'''
if hasattr(e, 'reason'):    # urlError
    print('We failed to reach a server')
    print('Reason: ', e.reason)
elif hasattr(e, 'code'):    # httpError
    print('The server could not fulfill the request.')
    print('Error code: ', e.code)
'''
