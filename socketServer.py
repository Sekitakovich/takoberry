import sys
import socketserver
import socket
import time
from queue import Queue


class Session(object):

    client = {}

    @classmethod
    def append(cls, *, port=None):
        cls.client[port] = Queue()
        print(cls.client)
        pass

    @classmethod
    def remove(cls, *, port=None):
        del(cls.client[port])
        print(cls.client)
        pass


class SampleHandler(socketserver.BaseRequestHandler):

    def setup(self):

        self.address = self.client_address[0]
        self.port = self.client_address[1]

        got = self.request.recv(80)
        name = got.decode()

        Session.append(port=self.port)

        print('connect: name = %s address = %s port = %s' % (name, self.address, self.port))
        pass

    def finish(self):
        Session.remove(port=self.port)
        print('Bye')
        pass

    def handle(self):

        client = self.request

        for counter in range(100):
            try:
                client.send(str(counter).encode())
                pass
            except socket.error as e:
                print(e)
                break
            else:
                time.sleep(1)


class SampleServer(socketserver.ThreadingTCPServer):

    def __init__(self, host='', port=0):
        super().__init__((host, port), SampleHandler)
        # print('init')

    def server_bind(self):

        self.timeout = 0
        self.allow_reuse_address = True

        # self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)


if __name__ == "__main__":

    # HOST = ''
    PORT = 12345

    server = SampleServer(host='', port=PORT)

    try:
        server.serve_forever()
    except KeyboardInterrupt as e:
        server.shutdown()
        server.server_close()
        sys.exit(0)
