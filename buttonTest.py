# Log temperature every 10 seconds
import smbus
import sqlite3
import time
import sys
import signal
import RPi.GPIO as GPIO

# constants
BUTTONONE = 16
BUTTONTWO = 12
BUTTONTHREE = 25
FILENAME = 'button.db'
TABLE = 'ButtonTime'
PERIOD = 1.0

# setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTONONE, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTONTWO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTONTHREE, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def timer_handler(signum, frame):
    ''' Periodic timer signal handler
    '''
    global db
    global cursor
    temp1 = False
    temp2 = False
    temp3 = False
    if GPIO.input(BUTTONONE): 
        temp1 = True
    if GPIO.input(BUTTONTWO): 
        temp2 = True
    if GPIO.input(BUTTONTHREE): 
        temp3 = True
    # Insert data into database
    sqlcmd="INSERT INTO {} VALUES (datetime('now','localtime'), {}, {}, {})".format(TABLE,temp1, temp2, temp3)
    cursor.execute(sqlcmd)
    sqlcmd="DELETE FROM {} WHERE datatime < datetime('now','localtime','-1 minute')".format(TABLE)
    cursor.execute(sqlcmd)
    db.commit()


# Connect to the database
db = sqlite3.connect(FILENAME)
cursor = db.cursor()

# Setup signal to call handler every PERIOD seconds
signal.signal(signal.SIGALRM, timer_handler)
signal.setitimer(signal.ITIMER_REAL, 1, PERIOD)

# Continuously loop blocking on signals
try:
    while True:
        signal.pause() # block on signal

except KeyboardInterrupt:
    db.close()
    print('Done')
