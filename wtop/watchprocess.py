import psutil

for pid in psutil.pids():
    process = psutil.Process(pid=pid)
    print(process.pid, process.name(), process.ppid())
    # if process.is_running():
    #     print('%d:%s %.1f %.1f' % (pid, process.name(), process.cpu_percent(), process.memory_percent()))