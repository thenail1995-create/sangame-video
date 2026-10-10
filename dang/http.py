"""Lop HTTP mong tren urllib. Moi module goi qua http.gui(...) nen test chi can patch mot ham."""
import json
import urllib.error
import urllib.parse
import urllib.request
import uuid

from . import chung


class LoiMang(Exception):
    pass


class Phan:
    def __init__(self, status, headers, body):
        self.status = status
        self.headers = {k.lower(): v for k, v in dict(headers).items()}
        self.body = body

    @property
    def text(self):
        return self.body.decode("utf-8", "replace")

    def json(self):
        try:
            v = json.loads(self.body.decode("utf-8", "replace"))
        except ValueError:
            return {}
        return v if isinstance(v, (dict, list)) else {}


class _KhongTheo(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def _multipart(truong, tep):
    ranh = "----sg" + uuid.uuid4().hex
    b = bytearray()
    for k, v in truong.items():
        b += f'--{ranh}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
    for k, (ten, noi_dung, mime) in tep.items():
        b += (f'--{ranh}\r\nContent-Disposition: form-data; name="{k}"; filename="{ten}"\r\n'
              f"Content-Type: {mime}\r\n\r\n").encode()
        b += noi_dung + b"\r\n"
    b += f"--{ranh}--\r\n".encode()
    return bytes(b), f"multipart/form-data; boundary={ranh}"


def gui(method, url, *, headers=None, params=None, json_body=None, form=None, data=None, files=None,
        timeout=60, theo_chuyen_huong=False) -> Phan:
    """Tra Phan cho moi ma HTTP (ke ca 4xx/5xx/3xx). Loi mang -> LoiMang (noi dung da che bi mat)."""
    hdr = dict(headers or {})
    if params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params, doseq=True)
    body = None
    if json_body is not None:
        body = json.dumps(json_body).encode()
        hdr.setdefault("Content-Type", "application/json; charset=UTF-8")
    elif files is not None:
        body, ct = _multipart(form or {}, files)
        hdr["Content-Type"] = ct
    elif form is not None:
        body = urllib.parse.urlencode(form).encode()
        hdr.setdefault("Content-Type", "application/x-www-form-urlencoded")
    elif data is not None:
        body = data
    req = urllib.request.Request(url, data=body, method=method, headers=hdr)
    opener = urllib.request.build_opener() if theo_chuyen_huong else urllib.request.build_opener(_KhongTheo)
    try:
        with opener.open(req, timeout=timeout) as r:
            return Phan(r.status, r.headers, r.read())
    except urllib.error.HTTPError as e:
        return Phan(e.code, e.headers, e.read())
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        goc = url.split("?")[0]
        raise LoiMang(chung.che(f"{method} {goc}: {type(e).__name__}")) from None
