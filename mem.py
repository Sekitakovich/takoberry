import psutil

mem = psutil.virtual_memory()

print(mem)

print(mem.used / mem.total)

print((mem.total - mem.available) / mem.total * 100)