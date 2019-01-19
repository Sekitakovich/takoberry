import serial

from common import Common


device = '/dev/serial0'

symbol = 'PMTK251'

thisValue = 19200
nextValue = 38400

body = symbol + ',' + str(nextValue)
print(body)
csum = Common.checkSum(body=body.encode())
print(hex(csum))
command = '$' + body + '*' + str(hex(csum))[2:] + '\r\n'
print(command)

b = command.encode()

port = serial.Serial(device, baudrate=thisValue, timeout=1)
port.write(b)

r = port.readline(1024)
print(r)


