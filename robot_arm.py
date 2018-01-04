import time
import uuid
import json
import logging
from AWSIoTPythonSDK.core.greengrass.discovery.providers import DiscoveryInfoProvider
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
from AWSIoTPythonSDK.exception.AWSIoTExceptions import subscribeQueueDisabledException

class RobotArm:
    ENDPOINT = 'greengrass.iot.ap-northeast-1.amazonaws.com'
    ROOT_CA_PATH = 'certs/robotArm/root-ca.pem'
    CERTIFICATE_PATH = 'certs/robotArm/c5e6d39f7b-certificate.pem.crt'
    PRIVATE_KEY_PATH = 'certs/robotArm/c5e6d39f7b-private.pem.key'
    THING_NAME = 'RobotArm_Thing'
    CLIENT_ID = 'RobotArm_Thing'
    GROUP_CA_PATH = './groupCA/'
    METERING_TOPIC = '/topic/state'

    def __init__(self):
        self.discoveryInfoProvider = DiscoveryInfoProvider()
        self.discoveryInfoProvider.configureEndpoint(self.ENDPOINT)
        self.discoveryInfoProvider.configureCredentials(self.ROOT_CA_PATH, self.CERTIFICATE_PATH, self.PRIVATE_KEY_PATH)
        self.discoveryInfoProvider.configureTimeout(10)

        logger = logging.getLogger('AWSIoTPythonSDK.core')
        logger.setLevel(logging.DEBUG)
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

    def get_device_shadow(self, shadowClient):
        return shadowClient.createShadowHandlerWithName(self.CLIENT_ID, True)

    def shadow_update_callback(self, payload, responseStatus, token):
        reportedState = json.loads(payload)['state']['reported']['myState']
        self.publish_mqtt_async(self.mqttClient, reportedState)

    def shadow_delta_callback(self, payload, responseStatus, token):
        desiredState = json.loads(payload)['state']['myState']
        self.publish_shadow_state(self.deviceShadow, desiredState)

    def publish_shadow_state(self, deviceShadow, state):
        reportedState = { 'state': { 'reported': { 'myState': state } } }
        print('Sending State -------\n%s' % reportedState)
        deviceShadow.shadowUpdate(json.dumps(reportedState), self.shadow_update_callback, 5)

    def publish_mqtt_async(self, mqttClient, state):
        payload = { 'state': state }
        mqttClient.publish(self.METERING_TOPIC, json.dumps(payload), 0)

    def wait_for_update_shadow(self, deviceShadow):
        deviceShadow.shadowRegisterDeltaCallback(self.shadow_delta_callback)

    def execute(self):
        groupId, ca, coreInfo = self.get_ggc_info()
        groupCAPath = self.write_ca_file(groupId, ca)

        shadowClient = self.connect_to_shadow_service(groupCAPath, coreInfo)

        self.deviceShadow = self.get_device_shadow(shadowClient)
        self.mqttClient = self.get_mqtt_client(shadowClient)

        self.publish_shadow_state(self.deviceShadow, 'off')

        self.wait_for_update_shadow(self.deviceShadow)
        print('Waiting for an update!')

        while True:
            time.sleep(1)

if '__main__' == __name__:
    robotArm = RobotArm()
    robotArm.execute()

