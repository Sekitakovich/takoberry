import socket
import time

host = '127.0.0.1'
port = 12345
buff = 1024


def make_connection(host_, port_):
    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.connect((host_, port_))
            print('connected')
            return sock
        except socket.error as e:
            print('failed to connect, try reconnect')
            time.sleep(1)


if __name__ == '__main__':

    s = make_connection(host, port)
    s.send(b'hello')

    for counter in range(75):
        try:
            m = s.recv(buff)
            if m:
                print(m)
                pass
            else:
                break
        except KeyboardInterrupt as e:
            print(e)
            break
        except socket.error as e:
            print(e)
            break
