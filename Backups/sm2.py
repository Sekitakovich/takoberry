from __future__ import absolute_import
import argparse
import time
from datetime import datetime as dt

import psutil
from colorama import Fore, Style


class SweetMemories(object):

    def __init__(self, **_3to2kwargs):

        if 'color' in _3to2kwargs: color = _3to2kwargs['color']; del _3to2kwargs['color']
        else: color = True
        if 'verbose' in _3to2kwargs: verbose = _3to2kwargs['verbose']; del _3to2kwargs['verbose']
        else: verbose = False
        if 'max' in _3to2kwargs: max = _3to2kwargs['max']; del _3to2kwargs['max']
        else: max = 0
        if 'min' in _3to2kwargs: min = _3to2kwargs['min']; del _3to2kwargs['min']
        else: min = 0
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
                except MemoryError, e:
                    color = Fore.YELLOW if self.color else u''
                    print color + u'!!! falied (allocation fault?)'
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
                    color = Fore.YELLOW if self.color else u''
                    print color + u'!!! failed (no blocks)'
                    time.sleep(1)
                pass

            else:
                if self.verbose:
                    if cc:
                        color = Fore.RED if self.color else u''
                        print color + u'+++ Charged %d blocks' % (cc,)
                        cc = 0
                        pass

                    if pc:
                        color = Fore.BLUE if self.color else u''
                        print color + u'+++ Purged %d blocks' % (pc,)
                        pc = 0
                        pass

                try:
                    color = Style.BRIGHT + Fore.WHITE if self.color else u''
                    at = dt.now().strftime(u'%Y-%m-%d %H:%M:%S')
                    print color + u'=== Using %.1f%% (A:T = %d:%d) holds %d at %s' % (
                        memory.percent, memory.available, memory.total, blocks, at)
                    time.sleep(1)
                except KeyboardInterrupt:
                    print u'Finished'
                    loop = False


if __name__ == u'__main__':

    parser = argparse.ArgumentParser(
        description=u'This script keeps used main-memmory between MIN and MAX',
        add_help=True,
    )

    parser.add_argument(u'--min', help=u'Minimum volume(%%)', type=float, default=50.0)
    parser.add_argument(u'--max', help=u'Maximum volume(%%)', type=float, default=51.0)
    parser.add_argument(u'-c', help=u'colorful output', action=u'store_true')
    parser.add_argument(u'-v', help=u'verbose output', action=u'store_true')

    args = parser.parse_args()

    if args.min >= args.max:
        print u'Parameter error - min(%f) >= max(%f)' % (args.min, args.max,)
    else:
        print u'Start on min(%.1f%%) max(%.1f%%)' % (args.min, args.max,)
        sm = SweetMemories(min=args.min, max=args.max, verbose=args.v, color=args.c)
        sm.start()
