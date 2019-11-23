import argparse
import time
from datetime import datetime as dt

import psutil
from colorama import Fore, Style


class SweetMemories(object):

    def __init__(self, *, min=0, max=0, verbose=False, color=True):

        self.min = min
        self.max = max
        self.verbose = verbose
        self.color = color

        self.blockSize = 100000
        self.fatman = []

    def start(self):

        loop = True
        cc = 0
        pc = 0

        while loop:

            memory = psutil.virtual_memory()
            blocks = len(self.fatman)

            if memory.percent < self.min:
                try:
                    self.fatman.append([0] * self.blockSize)
                    pass
                except MemoryError as e:
                    color = Fore.YELLOW if self.color else ''
                    print(color + '!!! falied (allocation fault?)')
                    time.sleep(1)
                    pass
                else:
                    cc += 1
                    pass

            elif memory.percent >= self.max:
                if blocks:
                    del (self.fatman[0])  # purge 1 entry
                    pc += 1
                    pass
                else:
                    color = Fore.YELLOW if self.color else ''
                    print(color + '!!! failed (no blocks)')
                    time.sleep(1)
                pass

            else:
                if self.verbose:
                    if cc:
                        color = Fore.RED if self.color else ''
                        print(color + '+++ Charged %d blocks' % (cc,))
                        cc = 0
                        pass

                    if pc:
                        color = Fore.BLUE if self.color else ''
                        print(color + '+++ Purged %d blocks' % (pc,))
                        pc = 0
                        pass

                try:
                    color = Style.BRIGHT + Fore.WHITE if self.color else ''
                    at = dt.now().strftime('%Y-%m-%d %H:%M:%S')
                    print(color + '=== Using %.1f%% (A:T = %d:%d) holds %d at %s' % (
                        memory.percent, memory.available, memory.total, blocks, at))
                    time.sleep(1)
                except KeyboardInterrupt:
                    print('Finished')
                    loop = False


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='This script keeps used main-memmory between MIN and MAX',
        add_help=True,
    )

    parser.add_argument('--min', help='Minimum volume(%%)', type=float, default=50.0)
    parser.add_argument('--max', help='Maximum volume(%%)', type=float, default=51.0)
    parser.add_argument('-c', help='colorful output', action='store_true')
    parser.add_argument('-v', help='verbose output', action='store_true')

    args = parser.parse_args()

    if args.min >= args.max:
        print('Parameter error - min(%f) >= max(%f)' % (args.min, args.max,))
    else:
        print('Start on min(%.1f%%) max(%.1f%%)' % (args.min, args.max,))
        sm = SweetMemories(min=args.min, max=args.max, verbose=args.v, color=args.c)
        sm.start()
