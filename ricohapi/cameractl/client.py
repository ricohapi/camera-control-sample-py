# -*- coding: utf-8 -*-
# Copyright (c) 2016 Ricoh Co., Ltd. All Rights Reserved.

"""
Camera remote control SDK
"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import re
from logging import getLogger, NullHandler, StreamHandler, DEBUG #pylint: disable=unused-import

import msgpack  #pylint: disable=import-error
from ricohapi.cameractl.mqtt_client import (Topic, MQTTClient, MQTTClientError)

LOG = getLogger(__name__)
LOG.addHandler(StreamHandler())
#LOG.setLevel(DEBUG)


class CamTopic(Topic):
    """A class to manage topics for camera control."""
    def __init__(self):
        super(CamTopic, self).__init__()
        self.cam_fmt = str('camera/{dev_id}')

    def remocon(self, dev_id):
        """Get camera control topic."""

        if dev_id is None:
            raise ValueError('dev_id is necessary.')
        else:
            topic = str(self.cam_fmt.format(dev_id=dev_id))

        return topic

    @staticmethod
    def validate_device_id(device_id=None):
        """validate "device id" with camera control topic format.

        :param: str device_id: device id you want to verify.
        """
        if device_id is None:
            return False

        acceptable = '[A-Za-z0-9_]{1,32}'
        try:
            match = re.match(acceptable, device_id)
            if match is None:
                return False
            else:
                return device_id == match.string[match.start(0):match.end(0)]
        except TypeError:
            raise TypeError
        except:
            raise Exception

    @staticmethod
    def search_dev_id(topic):
        """
        Get devid from topic.

        :param: str topic: topic
        :rtype: str(unicode in Python2)
        :returns: device id
        """
        pattern = r'(.+)/camera/'
        match = re.search(pattern, CamTopic.unescape_topic(topic))

        if match is None:
            raise ValueError('device id not found.')

        devid = topic[match.end():len(topic)]
        if not CamTopic.validate_device_id(devid):
            raise ValueError('device id is wrong.')

        try:
            devid = devid.decode('utf-8')
        except AttributeError:
            pass

        return devid


class Client(MQTTClient): #pylint: disable=too-many-instance-attributes
    """Ricoh camera remote control client.

    :param str client_id: your client id
    :param str client_secret: your client secret
    """
    def __init__(self, client_id, client_secret):
        super(Client, self).__init__(client_id, client_secret)
        self.__listened = False
        self.__sub_dev_id = None
        self.__func = None
        self.__args = ()
        self.cam_topic = CamTopic()

    def listen(self, device_id, func=None, fargs=None):
        """Start listening to the camera control messages
           and callbacks when the message is received.

        :param str device_id: device id to which you want to send message.
        :param function func: callback function which called message is received
        :param tuple fargs: func argument
        """

        if self.__listened:
            raise ClientError('already listened. If you want to change device to listen, '
                              'you should call unlisten().')
        if not self.__sub_dev_id is None:
            raise ClientError('The device id is already specified.')
        if not CamTopic.validate_device_id(device_id):
            raise ValueError('The device id is not acceptable.')

        self.__func = func
        self.__args = fargs if fargs else ()
        self.__sub_dev_id = device_id

        try:
            super(Client, self).subscribe(self.sub_cam_topic, func=self.__on_message, fargs=None)
        except MQTTClientError:
            raise ClientError
        except:
            raise
        self.__listened = True

    def unlisten(self):
        """Unlisten to the camera control message that is already listened.
        """
        if not self.__listened:
            LOG.warning('No device is listened. Do nothing.')
            return

        try:
            super(Client, self).unsubscribe()
        except MQTTClientError:
            raise ClientError
        except:
            raise
        self.__sub_dev_id = None
        self.__listened = False

    def shoot(self, device_id, param=None):
        """Send a shooting message to your device specified by the device_id.

        :param str device_id: a device id to which you want to send a message.
        :param dict param: user specified camera control parameters.
        """
        if not CamTopic.validate_device_id(device_id):
            raise ValueError('The device id is not acceptable.')

        topic = self.cam_topic.remocon(device_id)

        payload = {'c': 'shoot', 't': CamTopic.timestamp()}
        if not param is None:
            if not isinstance(param, dict):
                raise ValueError('param must be dictionary.')
            payload.update({'p': param})
        packed_msg = msgpack.packb(payload, encoding='utf-8', use_bin_type=True)
        packed_msg = bytearray(packed_msg)

        try:
            super(Client, self).publish(topic, message=packed_msg)
        except MQTTClientError:
            raise ClientError
        except:
            raise

    @property
    def sub_cam_topic(self):
        """Get camera control topic connected to the device ID.

        :rtype: str or None
        :returns: the camera control topic set in this instance.
        """
        if self.__sub_dev_id is None:
            return None
        else:
            topic = self.cam_topic.remocon(self.__sub_dev_id)
            return topic

    def __on_message(self, msg): #pylint: disable=unused-argument
        """The callback for when a PUBLISH message is received from the server.
        """
        unpacked = msgpack.unpackb(msg.payload, encoding='utf-8')
        LOG.debug('receive message. %s %s', msg.topic, unpacked)
        unpacked = dict(unpacked)

        if self.__func is None:
            return

        cmd = unpacked['c'] if 'c' in unpacked else None
        par = unpacked['p'] if 'p' in unpacked else None
        try:
            dev_id = CamTopic.search_dev_id(msg.topic)
        except ValueError:
            dev_id = 'DEVID_NOT_FOUND'

        self.__func(dev_id, cmd, par, *self.__args)


class ClientError(MQTTClientError):
    """Camera control client error"""
    pass

