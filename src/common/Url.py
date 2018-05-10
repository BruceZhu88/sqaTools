
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
        text = res.read().decode('utf8')
    except Exception as e:
        text = "error"
    return {"text": text, "status": status}


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
        """
        if hasattr(e, 'reason'):    # urlError
            print('We failed to reach a server')
            print('Reason: ', e.reason)
        elif hasattr(e, 'code'):    # httpError
            print('The server could not fulfill the request.')
            print('Error code: ', e.code)
        """