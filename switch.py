import sys
import time
import uuid
import json
import logging
from AWSIoTPythonSDK.core.greengrass.discovery.providers import DiscoveryInfoProvider
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient

class Switch:
    ENDPOINT = 'greengrass.iot.ap-northeast-1.amazonaws.com'
    ROOT_CA_PATH = 'certs/switch/root-ca.pem'
    CERTIFICATE_PATH = 'certs/switch/a20b621e05-certificate.pem.crt'
    PRIVATE_KEY_PATH = 'certs/switch/a20b621e05-private.pem.key'
    THING_NAME = 'Switch_Thing'
    CLIENT_ID = 'Switch_Thing'
    TARGET_THING_NAME = 'RobotArm_Thing'
    GROUP_CA_PATH = './groupCA/'

    def __init__(self):
        self.discoveryInfoProvider = DiscoveryInfoProvider()
        self.discoveryInfoProvider.configureEndpoint(self.ENDPOINT)
        self.discoveryInfoProvider.configureCredentials(self.ROOT_CA_PATH, self.CERTIFICATE_PATH, self.PRIVATE_KEY_PATH)
        self.discoveryInfoProvider.configureTimeout(10)

        logger = logging.getLogger('AWSIoTPythonSDK.core')
        logger.setLevel(logging.INFO)
        streamHandler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        streamHandler.setFormatter(formatter)
        logger.addHandler(streamHandler)

    def get_ggc_info(self):
        discoveryInfo = self.discoveryInfoProvider.discover(self.THING_NAME)
        caList = discoveryInfo.getAllCas()
        coreList = discoveryInfo.getAllCores()

        groupId, ca = caList[0]
        coreInfo = coreList[0]
        return (groupId, ca, coreInfo)

    def write_ca_file(self, groupId, ca):
        groupCAPath = self.GROUP_CA_PATH + groupId + '_CA_' + str(uuid.uuid4()) + '.crt'
        groupCAFile = open(groupCAPath, 'w')
        groupCAFile.write(ca)
        groupCAFile.close()
        return groupCAPath

    def connect_to_shadow_service(self, groupCAPath, coreInfo):
        shadowClient = AWSIoTMQTTShadowClient(self.CLIENT_ID)
        shadowClient.configureCredentials(groupCAPath, self.PRIVATE_KEY_PATH, self.CERTIFICATE_PATH)

        connectivityInfo = coreInfo.connectivityInfoList[0]
        ggcHost = connectivityInfo.host
        ggcPort = connectivityInfo.port

        shadowClient.configureEndpoint(ggcHost, ggcPort)
        shadowClient.connect()
        return shadowClient

    def get_mqtt_client(self, shadowClient):
        return shadowClient.getMQTTConnection()

    def update_target_device_shadow(self, mqttClient, state):
        update_topic = '$aws/things/%s/shadow/update' % self.TARGET_THING_NAME
        desiredState = { 'state': { 'desired': { 'myState': state } } }
        print('Sending State -------\n%s' % desiredState)
        mqttClient.publish(update_topic, json.dumps(desiredState), 0)

    def execute(self):
        groupId, ca, coreInfo = self.get_ggc_info()
        groupCAPath = self.write_ca_file(groupId, ca)

        shadowClient = self.connect_to_shadow_service(groupCAPath, coreInfo)

        mqttClient = self.get_mqtt_client(shadowClient)

        while True:
            sys.stdout.write('Please enter 1 (turn on) or 0 (turn off) to control the robot arm, q to quit: ')
            user_input = raw_input('')

            if user_input == 'q':
                break

            if user_input == '1':
                state = 'on'
            elif user_input == '0':
                state = 'off'
            else:
                print('Invalid input.')
                continue

            self.update_target_device_shadow(mqttClient, state)

if '__main__' == __name__:
    switch = Switch()
    switch.execute()

