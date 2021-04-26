import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt
import time
from threading import Thread, Lock

##### Change this string depending on the dorm the Pi resides in
LOCATION = "Kappa"
##### Change this string depending on the dorm the Pi resides in

HOUR = 60
HALF_HOUR = 30
BROKER = 'iot.cs.calvin.edu'
PORT = 8883
QOS = 2
USERNAME = 'cs326'
PASSWORD = 'piot'
CERTS = '/etc/ssl/certs/ca-certificates.crt'
WASHER1_PIN = 12
WASHER2_PIN = 16
DRYER1_PIN = 23
DRYER2_PIN = 25
#CYCLE_START_COUNT = 2
CYCLE_TIMEOUT_COUNT = 150
INTERVAL_SLEEP_TIMER = 1

def on_connect(userdata, rc, *extra_params):
    ''' Provides feedback upon connecting to MQTT. '''
    print("Connected with result code={}".format(rc))

def on_message(client, userdata, message):
    ''' 
    Upon receiving a request for machine states, determine if enough time has passed 
    since each machine's last rising edge to have come to a rest, then
    publish a string of binary values representing machine states to the appropriate MQTT topic.
    '''
    # determine if each machine is on, based upon the time of the last detected rising edge
    dryer1_status = (time.localtime().tm_hour) * HOUR + (time.localtime().tm_min) < timeDryer1 + HOUR
    dryer2_status = (time.localtime().tm_hour) * HOUR + (time.localtime().tm_min) < timeDryer2 + HOUR
    washer1_status = (time.localtime().tm_hour) * HOUR + (time.localtime().tm_min) < timeWasher1 + HALF_HOUR
    washer2_status = (time.localtime().tm_hour) * HOUR + (time.localtime().tm_min) < timeWasher2 + HALF_HOUR

    print("washer1 is ", washer1_status, " washer2 is ", washer2_status, " dryer1 is ", dryer1_status, " dryer2 is ", dryer2_status)
    client.publish("cs326/washroom/" + LOCATION, payload=str(int(washer1_status)) + str(int(washer2_status)) + str(int(dryer1_status)) + str(int(dryer2_status)) )

# initialize pins and washer status
GPIO.setmode(GPIO.BCM)
GPIO.setup(WASHER1_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(WASHER2_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(DRYER1_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(DRYER2_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
washer1_status = washer2_status = False

# time stamps for the washers and dryers
timeWasher1 = 0
timeWasher2 = 0
timeDryer1 = 0
timeDryer2 = 0

def watcher(pin_number):
    '''
    Upon detecting a rising edge for a washer or dryer pin, start a timer.
    If the prior rising edge was over an hour ago for dryers or half hour ago
    for washers, update the machine's time variable to the current time.
    '''
    global timeWasher1, timeWasher2, timeDryer1, timeDryer2
    if(pin_number == WASHER1_PIN):
        print(str(timeWasher1))
        if((time.localtime().tm_hour) * HOUR + (time.localtime().tm_min) > timeWasher1 + HALF_HOUR):
            timeWasher1 = (time.localtime().tm_hour) * HOUR + (time.localtime().tm_min)
    elif(pin_number == WASHER2_PIN):
        print(str(timeWasher2))
        if((time.localtime().tm_hour) * HOUR + (time.localtime().tm_min) > timeWasher2 + HALF_HOUR):
            timeWasher2 = (time.localtime().tm_hour) * HOUR + (time.localtime().tm_min)
    elif(pin_number == DRYER1_PIN):
        print(str(timeDryer1))
        if((time.localtime().tm_hour) * HOUR + (time.localtime().tm_min) > timeDryer1 + HOUR):
            timeDryer1 = (time.localtime().tm_hour) * HOUR + (time.localtime().tm_min)
    elif(pin_number == DRYER2_PIN):
        print(str(timeDryer2))
        if((time.localtime().tm_hour) * HOUR + (time.localtime().tm_min) > timeDryer2 + HOUR):
            timeDryer2 = (time.localtime().tm_hour) * HOUR + (time.localtime().tm_min)


# Detect a falling edge on input pin
GPIO.add_event_detect(WASHER1_PIN, GPIO.RISING, callback=watcher, bouncetime=250)
GPIO.add_event_detect(WASHER2_PIN, GPIO.RISING, callback=watcher, bouncetime=250)
GPIO.add_event_detect(DRYER1_PIN, GPIO.RISING, callback=watcher, bouncetime=250)
GPIO.add_event_detect(DRYER2_PIN, GPIO.RISING, callback=watcher, bouncetime=250)

# intialize mqtt client and mutex
client = mqtt.Client()
client.username_pw_set(USERNAME, password=PASSWORD)
client.tls_set(CERTS)
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, PORT, 60)
client.subscribe("cs326/washroom/" + LOCATION + "/request", qos=QOS)
client_mutex = Lock()

try:
    client.loop_forever()
except KeyboardInterrupt:
    client.disconnect()
    GPIO.cleanup()
