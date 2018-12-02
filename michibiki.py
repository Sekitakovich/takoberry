import serial


def checkSum(*, body=b''):
    cs = 0
    for v in body:
        cs ^= v

    return cs


def chop(*, raw=b''):
    try:
        src = raw.decode('ascii')
    except UnicodeDecodeError as e:
        print(e)
        pass
    else:

        if len(src) > 82:
            pass
        if len(src) <= 4:  # $*CS
            pass
        elif src[0] not in ('$', '!'):
            pass
        else:
            part = src.split('*')
            if len(part) != 2:
                pass
            else:
                body = part[0]
                csum = part[1]


def main():


    device = '/dev/serial0'
    baudrate = 9600

    min = len('$*CS')

    port = serial.Serial(device, baudrate=baudrate)

    while True:

        try:
            sentence = port.readline(1024).decode()  # bytes -> str
        except UnicodeDecodeError as e:
            print(e)
        else:
            if len(sentence) >= min:
                part = sentence.split('*')
                if len(part) == 2 and part[0][0] in ('$', '!'):
                    try:
                        csum = int(part[1][:2], 16)
                    except ValueError as e:
                        print(e)
                    else:

                        body = part[0][1:]
                        if csum == checkSum(body=body.encode()):
                            item = body.split(',')
                            print(item)
                        else:
                            print("Checksum not match")
                else:
                    print("Bad format")
            else:
                print("Bad format")

    return


if __name__ == '__main__':
    main()
