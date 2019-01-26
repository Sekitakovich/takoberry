import socket
import time
import json

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
    # s.send(b'hello')

    id = 0

    while True:
        try:
            raw = s.recv(buff)
            if raw:
                info = json.loads(raw.decode())
                counter = info['id']
                if counter == (id+1):
                    pass
                else:
                    print('Sequence error %d != %d' % (id+1, counter))
                print('%d: %s %s %s' % (info['id'], info['ymd'], info['hms'], info['nmea']))
                id = counter
                pass
            else:
                break
        except KeyboardInterrupt as e:
            print(e)
            break
        except socket.error as e:
            print(e)
            break
