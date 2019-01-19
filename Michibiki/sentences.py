import serial

# from Michibiki.common import Common
import Michibiki.common

device = '/dev/serial0'

symbol = 'PMTK314'

thisValue = 38400

body = symbol + ',' + '0,1,0,5,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0'
print(body)
csum = Michibiki.common.Common.checkSum(body=body.encode())
print(hex(csum))
command = '$' + body + '*' + str(hex(csum))[2:] + '\r\n'
print(command)

b = command.encode()

port = serial.Serial(device, baudrate=thisValue, timeout=1)
port.write(b)


