# Usage: python sensorVersion2.py -l -b -c -u -p
#    -l: Location (Dorm/apartment name)
#    -b: Broker address
#    -c: Broker cerificates (optional)
#    -u: Broker username (optional)
#    -p: Broker password (optional)
# This programs monitors 2 washers and 2 dryers.
# Uses cs326/washroom/Location/request for requests
# Uses cs326/washroom/Location for output
# Josh Ridder for cs326

import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt
import sys
import argparse
from help_string import HELP_STRING

HOUR = 60
HALF_HOUR = 30
PORT = 8883
QOS = 2
WASHER1_PIN = 12
WASHER2_PIN = 16
DRYER1_PIN = 23
DRYER2_PIN = 25

# parse arguments given to program 
parser = argparse.ArgumentParser()
parser.add_argument("-l", "--location", help="Dorm/Apartment name")
parser.add_argument("-b", "--broker", help="MQTT Broker")
parser.add_argument("-c", "--certs", help="Broker Certificates (optional)")
parser.add_argument("-u", "--username", help="Broker Username (optional)")
parser.add_argument("-p", "--password", help="Broker Password (optional)")
parser.add_argument("-h", "--help", help="Show help text")
args = parser.parse_args()

# print HELP_STRING and quit if not provided with necessary flags,
# or if called with help flag
if not args.location or not args.broker or args.help:
    print(HELP_STRING)
    sys.exit()

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
    client.publish("cs326/washroom/" + args.location, payload=str(int(washer1_status)) + str(int(washer2_status)) + str(int(dryer1_status)) + str(int(dryer2_status)) )

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

# set username and password if provided
if args.username and args.password:
    client.username_pw_set(args.username, password=args.password)
if args.certs:
    client.tls_set(args.certs)

# intialize mqtt client and mutex
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(args.broker, PORT, 60)
client.subscribe("cs326/washroom/" + args.location + "/request", qos=QOS)
client_mutex = Lock()

try:
    client.loop_forever()
except KeyboardInterrupt:
    client.disconnect()
    GPIO.cleanup()
