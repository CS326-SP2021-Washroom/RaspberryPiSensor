import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt
import time

BROKER = 'iot.cs.calvin.edu'
PORT = 1883
QOS = 0
USERNAME = 'cs326'
PASSWORD = 'piot'
INPUT_PIN = 12
OUTPUT_PIN = 16
CYCLE_TIMEOUT_COUNT = 10
CYCLE_START_COUNT = 4
ON = 1
OFF = 0

def on_sense_vibration(self):

    global client, sensor_count, currently_active
    print('call', sensor_count)
    # debug
    sensor_count += 1
    (result, num) = client.publish('cs326/basements/debug', str(sensor_count), qos=QOS)

    # sensor picked up motion
    if GPIO.input(INPUT_PIN) == ON:
        print('RISING?')
        #currently_active = True
        for second in range(CYCLE_START_COUNT):
            time.sleep(1)
            if GPIO.input(INPUT_PIN) == 0:
                print('NO RISE')
                return
        print('ROSE')
        (result, num) = client.publish('cs326/basements', time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime()), qos=QOS)
        GPIO.output(OUTPUT_PIN, ON) # debug
    # sensor stopped moving
    elif GPIO.input(INPUT_PIN) == OFF:
        print('FALLING?')
        for second in range(CYCLE_TIMEOUT_COUNT):
            time.sleep(1)
            if GPIO.input(INPUT_PIN) == 1:
                print('NO FALL')
                return
        print('FELL')
        #currently_active = False
        print("LOOP COMPLETE")
        (result, num) = client.publish('cs326/basements', 'OFF', qos=QOS)
        print(f'LED turned off')
        GPIO.output(OUTPUT_PIN, OFF) # debug
    if result != 0:
        print('PUBLISH returned error', result)
    #print("LED", GPIO.input(OUTPUT_PIN)) # debug

def on_connect(self, userdata, rc, *extra_params):
    print('Connected with result code={}'.format(rc))

# initialize pins
GPIO.setmode(GPIO.BCM)
GPIO.setup(INPUT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(OUTPUT_PIN, GPIO.OUT, initial=GPIO.LOW)

# sensor testing
sensor_count = 0
currently_active = False

# adds event detector to call on_sense_vibration
GPIO.add_event_detect(INPUT_PIN, GPIO.RISING, callback=on_sense_vibration, bouncetime=200)

client = mqtt.Client()
start_time = 0
client.username_pw_set(USERNAME, password=PASSWORD)
client.on_connect = on_connect
client.connect(BROKER, PORT, 60)

try:
    client.loop_forever()
except KeyboardInterrupt:
    client.disconnect()
    GPIO.cleanup()
    print("done")
