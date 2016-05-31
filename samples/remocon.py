# -*- coding: utf-8 -*-
# Copyright (c) 2016 Ricoh Co., Ltd. All Rights Reserved.
"""
Sample command line app for camera remote control.

USAGE
  remocon.py [options] command

COMMANDS
  shoot               send shooting message to your camera
  start               connect to ricoh vcp server

OPTIONS
  -h, --help          show this help message and exit.
  -d, --dev=DEVID     specify the device id
  -p, --param="str"   json string parameter to send with shooting, if need.

EXAMPLE
  python remocon.py -dDEV01 start
  python remocon.py -dDEV01 shoot
  python remocon.py -dDEV01 -p'{"_shutterSpeed": 0.01, "_iso": 200}' shoot

NOTE
  After a non-option argument, all further arguments are considered also non-options.
"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import sys
import json
import getopt
from logging import getLogger, NullHandler, StreamHandler #pylint: disable=unused-import
from logging import DEBUG, INFO #pylint: disable=unused-import
from ricohapi.cameractl.client import Client, ClientError

from thetav2 import ThetaV2
LOG = getLogger(__name__)
LOG.addHandler(StreamHandler())
LOG.setLevel(INFO)

def usage(message=None):
    """Show usage."""
    if not message is None:
        LOG.info(message)
    print(__doc__)
    raise sys.exit(0)


def validate_iso_and_shutter(iso=None, s_speed=None):
    """Validate iso value and shutter speed.

    Both iso value and shutter speed must be a pre-defined value.
    See the THETA developers site:
    https://developers.theta360.com/en/docs/v2/api_reference/

    :rtype: tuple, (int, int or float)
    :returns: iso and shutter speed which can be set to the RICOH THETA API v2.
    :raises: ValueError if parameters does not match the Theta v2 SDK format.
    """

    authorized_iso = [
        100, 125, 160, 200, 250, 320, 400, 500, 640, 800, 1000, 1250, 1600]

    authorized_ss = [
        0.00015625, 0.0002, 0.00025, 0.0003125, 0.0004, 0.0005,
        0.000625, 0.0008, 0.001, 0.00125, 0.0015625, 0.002,
        0.0025, 0.003125, 0.004, 0.005, 0.00625, 0.008,
        0.01, 0.0125, 0.01666666, 0.02, 0.025, 0.03333333,
        0.04, 0.05, 0.06666666, 0.07692307, 0.1, 0.125, 0.16666666, 0.2,
        0.25, 0.33333333, 0.4, 0.5, 0.625, 0.76923076, 1,
        1.3, 1.6, 2, 2.5, 3.2, 4, 5, 6, 8, 10, 13, 15, 20, 25, 30, 60]

    authorized_ss_frac = [
        '1/6400', '1/5000', '1/4000', '1/3200', '1/2500', '1/2000',
        '1/1600', '1/1250', '1/1000', '1/800', '1/640', '1/500',
        '1/400', '1/320', '1/250', '1/200', '1/160', '1/125',
        '1/100', '1/80', '1/60', '1/50', '1/40', '1/30',
        '1/25', '1/20', '1/15', '1/13', '1/10', '1/8', '1/6', '1/5',
        '1/4', '1/3', '1/2.5', '1/2', '1/1.6', '1/1.3', '1/1',
        '1.3/1', '1.6/1', '2/1', '2.5/1', '3.2/1', '4/1', '5/1',
        '6/1', '8/1', '10/1', '13/1', '15/1', '20/1', '25/1', '30/1', '60/1']

    if not iso is None:
        if not iso in authorized_iso:
            raise ValueError('Unsupported iso value.')

    if not s_speed is None:
        for (frac, speed) in zip(authorized_ss_frac, authorized_ss):
            if frac == s_speed:
                s_speed = speed
                break
            elif speed == s_speed:
                break
        else:
            raise ValueError('Unsupported shutter speed.')

        if (s_speed > 0.125) and (iso is None):
            raise ValueError('Both iso value and shutter speed should be specified '
                             'when the shutter speed is longer than 1/6 sec.')

    return (iso, s_speed)

def still_picture(iso=None, s_speed=None):
    """Take picture with user parameter.

    :param int or None iso: the ISO value to be set.
    :param int or str or None s_speed: the shutter speed to be set.
    """
    exp_program = {'manual': 1, 'normal': 2, 'ss': 4, 'iso': 9}

    if (iso is None) and (s_speed is None):
        exp_mode = 'normal'
    elif (not iso is None) and (not s_speed is None):
        exp_mode = 'manual'
    elif iso is None:
        exp_mode = 'ss'
    else:
        exp_mode = 'iso'

    iso, s_speed = validate_iso_and_shutter(iso, s_speed)

    options = {'exposureProgram': exp_program.get(exp_mode, 2),
               'captureMode': 'image'}

    if not iso is None:
        options.update({'iso': iso})
    if not s_speed is None:
        options.update({'shutterSpeed': s_speed})

    theta = ThetaV2()
    theta.set_options(**options)
    theta.take_picture()

def validate_usr_param(msg):
    """Validate the user message.

    :param str msg: string data to json stringfy.
                    msg must be json format on this sample.
    """
    if msg is None:
        return None

    if not isinstance(msg, str):
        raise ValueError('param "msg" must be string.')

    try: #json string to dict.
        par_converted = json.loads(msg)
        keys = par_converted.keys()
        for key in keys:
            if not key.startswith('_'):
                LOG.warning('key name should start with "_" %s.', key)
    except ValueError:
        raise ValueError('Could not convert to dictionary. '
                         'Parameter must be JSON string in this sample.')
    return par_converted

def wait_key():
    """return if enter key is input."""

    LOG.info('hit enter key to quit.')
    try:
        key_wait = raw_input #python2
    except NameError:
        key_wait = input #python3

    _ = key_wait()

def on_receive(devid, cmd, rcv_param, fun_param):
    """Called back when a camera control message is received.

    :param str or unicode(in Python2) devid: device id which is identified by received message.
    :param str or unicode(in Python2) cmd: now we supports only "shoot" command.
    :param dict or rcv_param: user specified callback function.
    :param fun_param: callback function arguments.
    """

    LOG.info('device   : %s', devid)
    LOG.info('command  : %s', cmd)
    LOG.info('rcv_param: %s', rcv_param)
    LOG.info('fun_param: %s', fun_param)

    if cmd != 'shoot':
        LOG.warning('Received unsupported cmd in this sample.')
        return
    else:
        iso, s_speed = None, None

        if not rcv_param is None:
            iq_param = dict(rcv_param)
            iso = iq_param.get('_iso', None)
            s_speed = iq_param.get('_shutterSpeed', None)

        result = 'failed'
        try:
            still_picture(iso, s_speed)
        except ValueError as err:
            LOG.warning(err)
        except Exception as err: #pylint: disable=broad-except
            LOG.warning(err)
        else:
            result = 'success'
        finally:
            LOG.debug('still picture %s.', result)

def main(): #pylint: disable=too-many-branches,too-many-locals
    """ main """
    dev_id = None
    send_param = None

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hd:p:', ['help', 'dev=', 'param='])
    except getopt.GetoptError as err:
        usage(err)

    if opts == []:
        usage('Specify options.')

    if len(args) != 1:
        LOG.warning('Warn: After a non-option argument,'\
                    ' all further arguments are considered also non-options')

    for option, arg in opts:
        if option in ('-h', '--help'):
            usage()
        elif option in ('-d', '--dev'):
            dev_id = arg
        elif option in ('-p', '--param'):
            send_param = arg
        else:
            usage('Unhandled option.')

    try:
        config_file = './config.json'
        with open(config_file, 'r') as settings:
            config = json.load(settings)
            user_id = config['USER']
            user_pass = config['PASS']
            client_id = config['CLIENT_ID']
            client_secret = config['CLIENT_SECRET']
            ca_certs = config['CA_CERTS']
    except IOError:
        raise ValueError('Could not read your config file. See the "./config_template.json"')

    if dev_id is None:
        usage('Specify device id.')

    if 'shoot' in args:
        with Client(client_id, client_secret) as camera:
            camera.connect(user_id, user_pass, ca_certs)
            camera.shoot(dev_id, param=validate_usr_param(send_param))
    elif 'start' in args:
        with Client(client_id, client_secret) as camera:
            camera.connect(user_id, user_pass, ca_certs)
            camera.listen(dev_id, func=on_receive, fargs=('callback_args',))
            LOG.info('connecting...')
            wait_key()
    else:
        usage('specify correct command')


if __name__ == '__main__':
    try:
        main()
    except ValueError as err:
        LOG.warning(err)
        sys.exit(-1)
    except ClientError as err:
        LOG.warning(err)
        sys.exit(-1)
    except SystemExit as err:
        sys.exit(err.args[0])
    except:
        raise
