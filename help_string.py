HELP_STRING = '''
Usage: <python-version> sensor.py [OPTIONS]

  -l, --location     The Dorm/Apartment the Pi is running in.
  -b, --broker       The MQTT broker to use.
  -c, --certs        The certification file to use with the MQTT broker. (optional)
  -u, --username     The username to use with the broker. (optional)
  -p, --password     The password to use with the broker. (optional)
  -h, --help         Display this help message. (optional)

Example:

  python3 sensor.py -l Gamma -b broker -b test.mosquitto.org
'''
