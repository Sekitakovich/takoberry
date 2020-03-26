import requests


class Burglar(object):

    def __init__(self):

        self.proxies = {
            'http': 'socks5://127.0.0.1:9050',
            'https': 'socks5://127.0.0.1:9050',
        }

    def shot(self, *, url: str, useTor: bool = False) -> str:

        result: str = ''

        try:
            got = requests.get(url=url, proxies=self.proxies if useTor else {})
        except (requests.exceptions.InvalidSchema,) as e:
            print(e)
        else:
            result = got.text

        return result


if __name__ == '__main__':
    
    b = Burglar()

    ipinfo: str = 'https://ipinfo.io'

    direct = b.shot(url=ipinfo)
    print(direct)

    withTor = b.shot(url=ipinfo, useTor=True)
    print(withTor)
