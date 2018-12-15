import time
from datetime import datetime as dt

import psutil
from colorama import Fore, Style

min = 70.0
max = 70.1

fatman = []
size = 100000

cc = 0
pc = 0

while True:

    memory = psutil.virtual_memory()
    thisblocks = len(fatman)

    if memory.percent < min:
        try:
            fatman.append([0] * size)
            pass
        except MemoryError as e:
            print(Fore.YELLOW + 'Give up (allocation fault?)')
            time.sleep(1)
            pass
            cc += 1
            pass

    elif memory.percent >= max:
        if thisblocks:
            del (fatman[0])  # purge 1 entry
            pc += 1
            pass
        else:
            print(Fore.YELLOW + 'Give up (no blocks)')
            time.sleep(1)
        pass

    else:
        if cc:
            print(Fore.RED + '+++ Charged %d' % (cc,))
            cc = 0
            pass

        if pc:
            print(Fore.BLUE + '+++ Purged %d' % (pc,))
            pc = 0
            pass

        at = dt.now().strftime('%Y-%m-%d %H:%M:%S')
        print(Style.BRIGHT + Fore.WHITE + '=== Using %.1f%% (%d/%d) holds %d at %s' % (
        memory.percent, memory.used / size, memory.total / size, thisblocks, at))
        time.sleep(1)
