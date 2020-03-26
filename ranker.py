import requests
from typing import Dict, List
from bs4 import BeautifulSoup
from dataclasses import dataclass
from datetime import datetime as dt
import subprocess
import time


@dataclass()
class Entry(object):
    title: str
    url: str


@dataclass()
class Result(object):
    status: int
    kw: str
    at: dt
    entry: List[Entry]


class Ranker(object):

    def __init__(self):

        self.urlBase: str = 'https://www.google.co.jp/search'
        self.proxies: Dict[str, str] = {
            'http': 'socks5://127.0.0.1:9050',
            'https': 'socks5://127.0.0.1:9050',
        }

        self.ip: str = ''
        self.hostname: str = ''

    def serviceTor(self, *, restart: bool = False):  # notice only Linux
        args = ['sudo', 'service', 'tor', 'restart' if restart else 'start']
        subprocess.call(args)

    def checkTor(self) -> bool:

        success: bool = False

        try:
            res = requests.get('https://ipinfo.io', proxies=self.proxies).json()
        except Exception as e:
            print(e)
        else:
            self.ip: str = res['ip']
            self.hostname: str = res['hostname'] if 'hostname' in res.keys() else '????'
            success = True

        return success

    def get(self, *, kw: str, count: int = 10, tor: bool = False) -> Result:

        result: Result = Result(kw='', at=dt.now(), entry=[], status=0)
        if kw:
            result.kw = kw
            option: Dict[str, any] = {
                'hl': 'ja',
                'num': count,
                'q': kw,
            }

            url = self.urlBase + '?' + '&'.join(['%s=%s' % (k, v) for k, v in option.items()])

            try:
                content = requests.get(url=url, proxies=self.proxies if tor else {})
            except Exception as e:
                print(e)
            else:
                status = content.status_code
                result.status = status
                if status == 200:
                    text = content.text
                    bs = BeautifulSoup(text, 'html.parser')
                    entry = bs.find_all("div", "ZINbbc xpd O9g5cc uUPGi")
                    for item in entry:
                        title = item.find("div", "BNeawe vvjwJb AP7Wnd")
                        if title:
                            url = (item.a.get("href").replace('/url?q=', '').split('&'))[0]
                            result.entry.append(Entry(title=title.string, url=url))
                else:
                    pass
                    # with open('text.html', 'rt',encoding='utf-8') as f:
                    #     f.write(content.text)

        return result


if __name__ == '__main__':

    useTor: bool = True

    french: List[str] = ['Debussy', 'Ravel', 'Poulenc', 'Honegger', 'Satie', 'Chabrier', 'Delibes',
                         'Faure', 'Pierne', 'Offenbach']
    other: List[str] = ['shostakovich', ]

    collector = Ranker()
    collector.serviceTor()

    while True:
        collector.checkTor()
        print('Using %s (%s)' % (collector.ip, collector.hostname))
        for name in french:
            try:
                ranking = collector.get(kw=name, tor=useTor)
            except KeyboardInterrupt as e:
                break
            else:
                if ranking.status == 200:
                    print(ranking)
                else:
                    print('Fault at status %d' % (ranking.status,))
                    collector.serviceTor(restart=True)
                    time.sleep(5)
                    break
