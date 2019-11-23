import RPi.GPIO as GPIO
import time

pin: int = 26

GPIO.setmode(GPIO.BCM)
GPIO.setup(pin, GPIO.OUT)

for x in range(2):
    GPIO.output(pin, True)
    time.sleep(2)
    GPIO.output(pin, False)
    time.sleep(2)

GPIO.cleanup()
