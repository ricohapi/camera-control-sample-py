# -*- coding: utf-8 -*-
# Copyright (c) 2016 Ricoh Co., Ltd. All Rights Reserved.
# pylint: disable=C0302
# pylint: disable=missing-docstring
#pylint: disable=protected-access
"""
Smoke test for client API.
"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from collections import namedtuple
from nose.tools import (assert_raises, eq_)
from nose.tools import assert_not_equal as neq_
from ricohapi.cameractl.client import CamTopic, Client, ClientError
from ricohapi.cameractl.mqtt_client import MQTTClient, MQTTClientError



class TestTopic(object):
    @staticmethod
    def test_devid():
        eq_(False, CamTopic.validate_device_id('+'))
        eq_(False, CamTopic.validate_device_id('#'))
        eq_(False, CamTopic.validate_device_id('abc#'))
        eq_(False, CamTopic.validate_device_id())
        eq_(False, CamTopic.validate_device_id('device/123'))
        eq_(True, CamTopic.validate_device_id('123'))
        eq_(True, CamTopic.validate_device_id('abcdefghabcdefghabcdefghabcdefgh'))
        eq_(False, CamTopic.validate_device_id('abcdefghabcdefghabcdefghabcdefgha'))
        eq_(True, CamTopic.validate_device_id(str('string')))
        eq_(True, CamTopic.validate_device_id(('abc')))
        eq_(False, CamTopic.validate_device_id('(abc)'))

        assert_raises(TypeError, CamTopic.validate_device_id, 123)
        assert_raises(TypeError, CamTopic.validate_device_id, {"abc":"123"})
        assert_raises(TypeError, CamTopic.validate_device_id, ['123'])
        assert_raises(TypeError, CamTopic.validate_device_id, ['DEV001', 'DEV002'])

    @staticmethod
    def test_search_devid():
        topic = CamTopic()
        eq_('devid01', CamTopic.search_dev_id(topic.topic('USER01', topic.remocon('devid01'))))
        neq_('devid02', CamTopic.search_dev_id(topic.topic('USER02', topic.remocon('devid01'))))
        assert_raises(ValueError, CamTopic.search_dev_id, 'user01/camera')
        assert_raises(ValueError, CamTopic.search_dev_id, 'user01/camera/')
        assert_raises(ValueError, CamTopic.search_dev_id, 'user01/camera/devid01/devid01')
        assert_raises(ValueError, CamTopic.search_dev_id, 'user01/camera//devid01')
        assert_raises(ValueError, CamTopic.search_dev_id, 'user01/camera/devid0#')

    @staticmethod
    def test_camera_topic():
        topic = CamTopic()
        devid = 'device001'
        uid = 'user01@example.com'
        assert_raises(ValueError, topic.remocon, None)
        eq_('camera/'+devid, topic.remocon(devid))
        eq_(uid+'/camera/'+devid, topic.topic(uid, topic.remocon(devid)))

    @staticmethod
    def test_timestamp():
        import time
        import datetime
        now = datetime.datetime.now()
        time1 = int(time.mktime(now.timetuple()))
        assert CamTopic.timestamp() >= time1

    @staticmethod
    def test_unescape_topic():
        topic = CamTopic()
        eq_('+#/%', topic.unescape_topic('%2B%23%2F%25'))

    @staticmethod
    def test_escape_topic():
        topic = CamTopic()
        eq_('%2B%23%2F%25', topic.escape_username('+#/%'))

class TestRemoteControl(object):
    @staticmethod
    def test_connect():
        client_id, client_secret = None, None
        user_id, user_pass, ca_certs = None, None, None
        with Client(client_id, client_secret) as camera:
            assert_raises(Exception, camera.connect, user_id, user_pass, ca_certs)

        with MQTTClient(client_id, client_secret) as camera:
            camera._MQTTClient__connected = True
            assert_raises(MQTTClientError, camera.connect, user_id, user_pass, ca_certs)


    @staticmethod
    def test_listen():
        client_id, client_secret = None, None
        camera = Client(client_id, client_secret)
        assert_raises(ClientError, camera.listen, 'DEVTEST', func=None, fargs=None)

        camera._Client__mqtt = object()
        camera._Client__connected = True
        assert_raises(ClientError, camera.listen, 'DEVID_%_NG', func=None, fargs=None)

        camera._Client__sub_dev_id = 'ALREADY_LISTENED'
        assert_raises(ClientError, camera.listen, 'DEVTEST', func=None, fargs=None)

        camera._Client__sub_dev_id = 'INVLID_DEVID_+'
        assert_raises(ClientError, camera.listen, 'DEVTEST', func=None, fargs=None)

        camera._Client__listening = True
        assert_raises(ClientError, camera.listen, 'DEVTEST', func=None, fargs=None)

    @staticmethod
    def test_disconnect1():
        client_id, client_secret = None, None

        with MQTTClient(client_id, client_secret) as mqtt:
            mqtt._MQTTClient__mqtt = object()
            mqtt._MQTTClient__connected = True
            mqtt._MQTTClient__listening = True
            mqtt.disconnect()

    @staticmethod
    def test_disconnect2():
        client_id, client_secret = None, None
        camera = Client(client_id, client_secret)
        eq_(None, camera.disconnect())


    @staticmethod
    def test_unlisten():
        client_id, client_secret = None, None
        camera = Client(client_id, client_secret)
        eq_(None, camera.unlisten())

        camera._Client__listening = True
        assert_raises(ClientError, camera.unlisten)


    @staticmethod
    def test_shoot():
        client_id, client_secret = None, None
        camera = Client(client_id, client_secret)
        assert_raises(ClientError, camera.shoot, 'DEV001')

        camera._Client__connected = True
        assert_raises(ValueError, camera.shoot, 'DEV%')

        assert_raises(ValueError, camera.shoot, 'DEV002', param="abc")

        assert_raises(ClientError, camera.shoot, 'DEV002', param={"_iso": 100})

    @staticmethod
    def test_subscribed_topic():
        client_id, client_secret = None, None
        camera = Client(client_id, client_secret)
        eq_(None, camera.sub_cam_topic)

        camera._Client__sub_dev_id = 'TESTDEVID'
        camera._Client__uid = 'user01'
        eq_('camera/TESTDEVID', camera.sub_cam_topic)

        camera._Client__uid = 'user01@example.com'
        eq_('camera/TESTDEVID', camera.sub_cam_topic)


    @staticmethod
    def test_client_keyborad_interrupt():
        try:
            client_id, client_secret = None, None
            with Client(client_id, client_secret):
                raise KeyboardInterrupt
        except KeyboardInterrupt:
            pass
        except: #pylint: disable=bare-except
            assert False

    @staticmethod
    def test_unpack_msg():
        import msgpack   #pylint: disable=import-error
        def on_receive(devid, cmd, rcv_param):  #pylint: disable=unused-argument
            pass
        payload = {'c': 'shoot', 't': CamTopic.timestamp()}
        packed_msg = msgpack.packb(payload, encoding='utf-8', use_bin_type=True)
        packed_msg = bytearray(packed_msg)
        message = namedtuple('message', ['topic', 'payload'])
        topic = CamTopic()
        msg = message(topic.remocon(dev_id='DEV001'), packed_msg)

        client_id, client_secret = None, None

        with Client(client_id, client_secret) as client:
            client._Client__func = on_receive
            client._Client__args = ()
            client._Client__on_message(msg)

        with Client(client_id, client_secret) as client:
            client._Client__func = None
            client._Client__args = ()
            eq_(None, client._Client__on_message(msg))
