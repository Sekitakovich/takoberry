import time
import wiringpi as wp


def main():

    pin = 26

    wp.wiringPiSetupGpio()
    wp.pinMode(pin, 1)

    while True:
        try:
            wp.digitalWrite(pin, 0)
            time.sleep(1)
            wp.digitalWrite(pin, 1)
            time.sleep(1)

        except KeyboardInterrupt:
            for a in range(3):
                wp.digitalWrite(pin, 1)
                time.sleep(0.2)
                wp.digitalWrite(pin, 0)
                time.sleep(0.2)
            break

    return


if __name__ == '__main__':

    main()
