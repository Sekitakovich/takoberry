import time
import board
import busio
import adafruit_adxl34x

if __name__ == '__main__':

    i2c = busio.I2C(board.SCL, board.SDA)
    accelerometer = adafruit_adxl34x.ADXL345(i2c, address=0x1D)
    accelerometer.enable_tap_detection(threshold=10)
    accelerometer.enable_motion_detection(threshold=20)

    for counter in range(30):
        print("%f %f %f" % accelerometer.acceleration)
        if accelerometer.events['tap']:
            print('Tapped')
        if accelerometer.events['motion']:
            print('Motion')
        time.sleep(0.5)

