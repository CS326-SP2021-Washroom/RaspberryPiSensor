# Usage: python sensor.py -l -b -c -u -p
#    -l: Location (Dorm/apartment name)
#    -b: Broker address
#    -c: Broker cerificates (optional)
#    -u: Broker username (optional)
#    -p: Broker password (optional)
# This programs monitors 2 washers and 2 dryers.
# Uses cs326/washroom/Location/request for requests
# Uses cs326/washroom/Location for output
# Josh Ridder for cs326
# 4-23-21

import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt
import sys
import argparse
from time import sleep
from threading import Thread, Lock
from help_string import HELP_STRING

PORT = 8883
QOS = 2
WASHER1_PIN = 12
WASHER2_PIN = 16
DRYER1_PIN = 23
DRYER2_PIN = 25
CYCLE_START_COUNT = 3
CYCLE_TIMEOUT_COUNT = 120
INTERVAL_SLEEP_TIMER = 1

# read arguments
parser = argparse.ArgumentParser()
parser.add_argument("-l", "--location", help="Dorm/Apartment name")
parser.add_argument("-b", "--broker", help="MQTT Broker")
parser.add_argument("-c", "--certs", help="Broker Certificates (optional)")
parser.add_argument("-u", "--username", help="Broker Username (optional)")
parser.add_argument("-p", "--password", help="Broker Password (optional)")
args = parser.parse_args()

if not args.location or not args.broker:
    print(HELP_STRING)
    sys.exit()

def on_connect(userdata, rc, *extra_params):
    ''' Provides feedback upon connecting to MQTT. '''
    print("Connected with result code={}".format(rc))

def on_message(client, userdata, message):
    '''
    Upon receiving a request for machine states, retrieve the current state of washers and dryers,
    then publish a string of binary values representing machine states to the appropriate MQTT topic.
    '''
    dryer1_status = GPIO.input(DRYER1_PIN) == False
    dryer2_status = GPIO.input(DRYER2_PIN) == False
    print("washer1 is ", washer1_status, " washer2 is ", washer2_status, " dryer1 is ", dryer1_status, " dryer2 is ", dryer2_status)
    client.publish("cs326/washroom/" + args.location, payload=str(int(washer1_status)) + str(int(washer2_status)) + str(int(dryer1_status)) + str(int(dryer2_status)) )

# initialize pins and washer status
GPIO.setmode(GPIO.BCM)
GPIO.setup(WASHER1_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(WASHER2_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(DRYER1_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(DRYER2_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
washer1_status = washer2_status = False

def monitor_washer(washer_pin_number):
    '''
    Used by washer threads to determine whether washers are currently on.
    Washers must stay on for CYCLE_START_COUNT seconds to register as on,
    and must stay off for CYCLE_TIMEOUT_COUNT seconds to register as off.
    '''
    global washer1_status, washer2_status, client, client_mutex
    while True:
        if GPIO.input(washer_pin_number):
            # Waits for CYCLE_TIMEOUT_COUNT seconds of continuous stillness before changing washer state to off
            for second in range(CYCLE_TIMEOUT_COUNT):
                client_mutex.acquire()
                client.loop()
                client_mutex.release()
                sleep(1)
                if not GPIO.input(washer_pin_number):
                    break
            else:
            # entire loop completed; change machine state to off
                if washer_pin_number == WASHER1_PIN:
                    washer1_status = False
                elif washer_pin_number == WASHER2_PIN:
                    washer2_status = False
        else:
            # Waits for CYCLE_START_COUNT seconds of continuous motion before changing washer state to on:
            for second in range(CYCLE_START_COUNT):
                client_mutex.acquire()
                client.loop()
                client_mutex.release()
                sleep(1)
                if GPIO.input(washer_pin_number):
                    break
            else:
            # entire loop completed; change machine state to on
                if washer_pin_number == WASHER1_PIN:
                    washer1_status = True
                elif washer_pin_number == WASHER2_PIN:
                    washer2_status = True
       # sleep(INTERVAL_SLEEP_TIMER)

# create a thread for each machine
washer_thread_one = Thread(target = monitor_washer, args=(WASHER1_PIN, ) )
washer_thread_two = Thread(target = monitor_washer, args=(WASHER2_PIN, ) )

# intialize mqtt client and mutex
client = mqtt.Client()
if args.username and args.password:
    client.username_pw_set(args.username, password=args.password)
if args.certs:
    client.tls_set(args.certs)
client.on_connect = on_connect
client.on_message = on_message
client.connect(args.broker, PORT, 60)
client.subscribe("cs326/washroom/" + args.location + "/request", qos=QOS)
client_mutex = Lock()

try:
    washer_thread_one.start()
    washer_thread_two.start()
except KeyboardInterrupt:
    client.disconnect()
    GPIO.cleanup()
