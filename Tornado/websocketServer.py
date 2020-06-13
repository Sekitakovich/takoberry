from threading import Lock
from tornado import ioloop, web, websocket
import wsaccel

from loguru import logger


class WebsocketServer(websocket.WebSocketHandler):
    client = {}
    locker = Lock()

    def open(self):
        key = id(self)
        with self.locker:
            if key not in self.client.keys():
                self.client[key] = self
                logger.debug('%d has come' % key)

    def on_message(self, message):
        key = id(self)
        logger.debug('from %d: %s' % (key, message))
        with self.locker:
            for k, v in self.client.items():
                if k != key:
                    v.write_message(message=message)

    def on_close(self):
        key = id(self)
        with self.locker:
            del self.client[key]
        logger.debug('%d was gone' % key)

    def check_origin(self, origin):  # これがないと403(謎)
        return True


if __name__ == '__main__':

    port = 8080
    host = '0.0.0.0'
    uri = '/ws'

    wsaccel.patch_tornado()  # See https://methane.hatenablog.jp/entry/2013/02/20/wsaccel_%E3%82%92_Tornado_%E3%81%AB%E5%AF%BE%E5%BF%9C%E3%81%97%E3%81%BE%E3%81%97%E3%81%9F

    app = web.Application([
        (uri, WebsocketServer)  # service only websocket
    ])

    logger.debug('Start service at %s:%d %s' % (host, port, uri))
    try:
        app.listen(port=port, address=host)
        ioloop.IOLoop.current().start()
    except (OSError, KeyboardInterrupt) as e:
        logger.debug(e)
