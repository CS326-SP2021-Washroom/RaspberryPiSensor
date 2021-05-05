# RaspberryPiSensor
Workspace for the backend of the Washroom app. The final Washroom project uses a smartphone application and a Raspberry Pi running sensor.py wired up to several vibration sensors that are affixed to washers and dryers on Calvin's campus. When users want to check the status of the machines, the app sends a request to the Pi using MQTT. The Pi will then publish the current status to the appropriate MQTT topic.
# Usage
Call sensor.py or sensorVersion2.py with at least the location and broker flags - for example:
```
python sensor.py -l Kappa -b test.mosquitto.org
```
