
import qrcode


class MakeQR(object):
    def __init__(self, path, version=1, box_size=5, border=1):
        self.version = version
        self.box_size = box_size
        self.border = border
        self.path = path

    def generate(self, txt):
        qr = qrcode.main.QRCode(version=self.version, box_size=self.box_size, border=self.border)
        qr.add_data(txt)
        qr.make(fit=True)
        m = qr.make_image()
        m.save(self.path)
        # print('ok,please check your source folder and check the pic.')


if __name__ == '__main__':
    text = "http://v.youku.com/v_show/id_XMTQ2MTE2MTUwMA==.html?spm=a2hzp.8244740.0.0&from=y1.7-1.2"
    makeQr = MakeQR("./qr.jpg")
    makeQr.generate(text)
