# -*- coding: utf-8 -*-
# Copyright (c) 2016 Ricoh Co., Ltd. All Rights Reserved.

"""
Camera remote control SDK
"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from collections import namedtuple
from logging import getLogger, NullHandler, StreamHandler, DEBUG #pylint: disable=unused-import

import datetime
import time
import uuid
import paho.mqtt.client as mqtt
from ricohapi.auth.client import AuthClient

LOG = getLogger(__name__)
LOG.addHandler(StreamHandler())
#LOG.setLevel(DEBUG)

ESCAPE_TRANSFORMATIONS = {'+': '%2B',
                          '#': '%23',
                          '/': '%2F',
                          '%': '%25'}

UNESCAPE_TRANSFORMATIONS = {'%2B': '+',
                            '%23': '#',
                            '%2F': '/',
                            '%25': '%'}

class Topic(object):
    """A class to manage topics."""
    def __init__(self):
        self.topic_fmt = str('{uid}/{topic}')

    def topic(self, user_id, topic):
        """Get topic."""
        uid = Topic.escape_username(user_id)
        return str(self.topic_fmt.format(uid=uid, topic=topic))

    @staticmethod
    def escape_username(username):
        """Escape of the local portion of a username."""
        result = []
        for i, char in enumerate(username):
            result.append(char)

        for i, char in enumerate(username):
            result[i] = ESCAPE_TRANSFORMATIONS.get(char, char)

        escaped = ''.join(result)

        return escaped

    @staticmethod
    def unescape_topic(topic):
        """Unescape of the local portion of a topic."""
        result = []
        seq = ''
        for i, char in enumerate(topic):
            if char == '%':
                seq = topic[i:i+3]
            if seq:
                if len(seq) == 3:
                    result.append(UNESCAPE_TRANSFORMATIONS.get(seq, char))

                seq = seq[1:]
            else:
                result.append(char)

        unescaped = ''.join(result)

        return unescaped

    @staticmethod
    def timestamp():
        """Return timestamp, if passed.

        :rtype: int
        :returns: Unix epoch
        """
        now = datetime.datetime.now()
        return int(time.mktime(now.timetuple()))

class MQTTClient(object): #pylint: disable=too-many-instance-attributes
    """Ricoh MQTT service client.
       This client program uses Eclipse Paho MQTT Python Client library.

    :param str client_id: your client id
    :param str client_secret: your client secret
    """
    def __init__(self, client_id, client_secret):
        self.__sub_topic = None
        self.__mqtt = None
        self.__connected = False
        self.__listened = False
        self.__client = {'id': client_id, 'secret': client_secret}
        self.__func = None
        self.__args = ()
        self.__topic = Topic()
        self.__uid = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is KeyboardInterrupt:
            pass
        elif not exc_type is None:
            LOG.debug(exc_type)
            LOG.debug(exc_value)

        if isinstance(self.__mqtt, mqtt.Client):
            self.__mqtt.loop_stop()
            self.__mqtt.disconnect()

        LOG.debug('terminated.')

    def connect(self, user_id, user_pass, ca_certs):
        """connect to the ricoh vcp server for using mqtt service.

        :param str user_id: your user id
        :param str user_pass: your password
        :param str ca_certs: The path to the ca certificate file.
        """
        if self.__connected:
            raise MQTTClientError('already connected to the server.')

        mqtts = self.__get_broker_info(user_id, user_pass)

        mqtt_cid = str(uuid.uuid4())
        self.__uid = user_id
        self.__mqtt = mqtt.Client(mqtt_cid)
        self.__mqtt.username_pw_set(mqtts.uid, mqtts.token)
        self.__mqtt.tls_set(ca_certs)
        self.__mqtt.connect(mqtts.host, mqtts.port, keepalive=60)
        self.__mqtt.message_retry_set(60)
        self.__mqtt.loop_start()
        self.__connected = True

    def disconnect(self):
        """Disconnect from the ricoh vcp server.
        """
        if (self.__mqtt is None) or (not self.__connected):
            LOG.debug(self.__mqtt)
            LOG.debug(self.__connected)
            LOG.warning('No client is connected to the server.')
            return

        if self.__listened:
            self.unsubscribe()

        if isinstance(self.__mqtt, mqtt.Client):
            self.__mqtt.loop_stop()
            self.__mqtt.disconnect()
            self.__mqtt = None
            self.__connected = False

    def subscribe(self, topic, func=None, fargs=None):
        """Subscribe to a topic.
           A Callback function is called when the client receives a message from the server.

        :param str topic: topic to which you want to send message.
        :param function func: callback function which is called when a message is received
        :param tuple fargs: func argument
        """

        if (self.__mqtt is None) or (not self.__connected):
            raise MQTTClientError('connect to the server before calling subscribe()')

        if self.__listened:
            LOG.warning('already listened. Do nothing.')
            return

        self.__func = func
        self.__args = fargs if fargs else ()
        self.__mqtt.on_message = self.__on_message
        self.__sub_topic = self.__topic.topic(self.__uid, topic)
        self.__subscribe(self.__sub_topic)
        self.__listened = True

    def unsubscribe(self):
        """Unsubscribe a topic which is already subscribed to.
        """
        if self.__mqtt is None:
            raise MQTTClientError('mqtt client is not initialized.')

        if not self.__listened:
            LOG.warning('No device is subscribed. Do nothing.')

        if isinstance(self.__mqtt, mqtt.Client):
            self.__mqtt.unsubscribe(self.__sub_topic)
            self.__sub_topic = None
            self.__listened = False

    def publish(self, topic, message=None):
        """Send a message from the client to the server.

        :param str device_id: a device id to which you want to send a message.
        :message dict param: user specified message.
        """

        if not self.__connected:
            raise MQTTClientError('You should connect to the server before calling publish()')

        topic = self.__topic.topic(self.__uid, topic)

        self.__send_message(topic, message)

    def __on_message(self, _client, _userdata, msg): #pylint: disable=unused-argument
        """The callback for when a PUBLISH message is received from the server.
        """
        LOG.debug('receive message. %s', msg.topic)

        if self.__func is None:
            return

        self.__func(msg, *self.__args)

    def __subscribe(self, topic, qos=1):
        """Subscribe to a topic specified by the argument.
           Note QOS 2 is not suppourted.
        """

        if self.__mqtt is None:
            raise MQTTClientError('mqtt client is not initialized.')

        if isinstance(topic, list):
            self.__mqtt.subscribe(topic)
        else:
            self.__mqtt.subscribe((topic, qos))
        LOG.debug('subscribe: %s', topic)

    def __send_message(self, topic, msg, qos=1):
        """send message."""
        if self.__mqtt is None:
            raise MQTTClientError('mqtt client is not initialized.')

        self.__mqtt.publish(topic, msg, qos, False)

    def __get_broker_info(self, user_id, user_pass):
        """Get some broker access information.

        :rtype: namedtuple
        :returns: Ricoh MQTT server access info.
        """

        auth_client = AuthClient(self.__client['id'], self.__client['secret'])
        auth_client.set_resource_owner_creds(user_id, user_pass)

        response = auth_client.session(AuthClient.SCOPES['CameraCtl'])

        if not 'access_token' in response:
            raise ValueError

        try:
            tmp = response['endpoints']['mqtts']
            tmp = tmp.split('mqtts://', 1)
            host = tmp[1].split(':', 1)[0]
            tmp = tmp[1].split(':', 1)[1]
            port = tmp.split('/')[0]

        except Exception as err:
            LOG.debug(err)
            raise

        token = auth_client.get_access_token()

        mqtt_inf = namedtuple('inf', ['uid', 'cid', 'token', 'host', 'port'])

        return mqtt_inf(user_id, self.__client['id'], token, host, int(port))


class MQTTClientError(Exception):
    """MQTT client error"""
    pass

