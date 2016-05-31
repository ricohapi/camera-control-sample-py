# -*- coding: utf-8 -*-
# Copyright (c) 2016 Ricoh Co., Ltd. All Rights Reserved.

"""RICOH THETA API v2 simple wrapper module"""
from __future__ import print_function
from logging import getLogger, StreamHandler
import os
import json
import requests
LOG = getLogger(__name__)
LOG.addHandler(StreamHandler())

class ThetaV2(object):
    """RICOH THETA API v2 simple wrapper class"""
    def __init__(self, base_url='http://192.168.1.1'):
        """Init instance.

        :param str base_url: (optional) base url of theta
        """
        self.base_url = base_url

    def get_info(self):
        """Acquires basic information about the camera and supported function.

        :rtype: dict
        """

        url = self.base_url + '/osc/info'
        LOG.debug(url)
        req = requests.get(url)
        req.raise_for_status()
        return req.json()

    def get_state(self):
        """Acquires the camera status.

        :rtype: dict
        """

        url = self.base_url + '/osc/state'
        LOG.debug(url)
        req = requests.post(url)
        req.raise_for_status()
        return req.json()

    def check_for_updates(self, state_fingerprint):
        """Acquires the current status ID, and checks for changes to the status.

        :param str state_fingerprint: Status ID
        :rtype: dict
        """

        url = self.base_url + '/osc/checkForUpdates'
        payload = json.dumps({'stateFingerprint': state_fingerprint})
        LOG.debug(url + ', ' + payload)
        req = requests.post(url, data=payload)
        req.raise_for_status()
        return req.json()

    def __execute_on_session(self, command, **params):
        """Executes the command on session.

        :param str command: Command to execute
        :param dict params: Input parameters required to execute each command
        :rtype: :class:`requests.Response`
        """
        params['sessionId'] = self.__start_session()
        try:
            req = self.__execute(command, **params)
        finally:
            self.__close_session(params['sessionId'])
        return req

    def __execute(self, command, **params):
        """Executes the command.

        :param str command: Command to execute
        :param dict params: Input parameters required to execute each command
        :rtype: :class:`requests.Response`
        """

        url = self.base_url + '/osc/commands/execute'
        payload = json.dumps({
            'name': command,
            'parameters': params
        })
        LOG.debug(url + ', ' + payload)
        req = requests.post(url, stream=True, data=payload)
        req.raise_for_status()
        return req

    def get_command_status(self, command_id):
        """Acquires the execution status of the command.

        :param str command_id: Command ID
        :rtype: dict
        """

        url = self.base_url + '/osc/commands/status'
        payload = json.dumps({'id': command_id})
        LOG.debug(url + ', ' + payload)
        req = requests.post(url, data=payload)
        req.raise_for_status()
        return req.json()

    def __start_session(self):
        """Starts the session. Issues the session ID.

        :return: Session ID
        :rtype: str
        """
        req = self.__execute('camera.startSession')
        return req.json()['results']['sessionId']

    def __close_session(self, session_id):
        """Closes the session.

        :return: Session ID
        :rtype: dict
        """
        req = self.__execute('camera.closeSession', sessionId=session_id)
        return req.json()

    def get_options(self, *option_names):
        """Acquires the properties and property support specifications
            for shooting, the camera, etc.

        :param option_names: option name list to be acquired
        :type option_names: tuple of str
        :rtype: dict
        """

        req = self.__execute_on_session('camera.getOptions', optionNames=option_names)
        return req.json()

    def set_options(self, **options):
        """Property settings for shooting, the camera, etc.

        :param dict options: Set of option names and setting values to be set
        :rtype: dict
        """
        req = self.__execute_on_session('camera.setOptions', options=options)
        return req.json()

    def take_picture(self):
        """Starts still image shooting.

        :rtype: dict
        """

        req = self.__execute_on_session('camera.takePicture')
        return req.json()

    def take_picture_to_file(self, save_path=None, delete_file=False, override_file=False):
        """Starts still image shooting and acquires image.

        :param str save_path: (optional) save file path.
        :param bool delete_file: (optional) if ``True``, image in theta will be deleted
                            after transfered. default to ``False``.
        :param bool override_file: (optional) if ``True``, the same name file will be overridden
        """
        finger = self.get_state()['fingerprint']

        # take picture
        command_id = self.take_picture()['id']

        # wait
        while self.check_for_updates(finger)['stateFingerprint'] == finger:
            pass

        progress = 'inProgress'
        while progress == 'inProgress':
            command_status = self.get_command_status(command_id)
            progress = command_status['state']

        if progress != 'done':
            raise ThetaError('Failed to take picture')

        # download
        file_uri = command_status['results']['fileUri']
        image = self.get_image(file_uri)

        # save
        if save_path is None:
            save_path = file_uri

        if not override_file and os.path.exists(save_path):
            raise OSError('File exists: ' + save_path)

        dir_path = os.path.abspath(os.path.dirname(save_path))
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        with open(save_path, 'wb') as fptr:
            fptr.write(image)

        # delete
        if delete_file:
            self.delete(file_uri)

    def get_image(self, file_uri):
        """Acquires images.

        :param str file_uri: ID of the file to be acquired
        :rtype: bytes
        """
        return self.__execute('camera.getImage', fileUri=file_uri).content

    def delete(self, file_uri):
        """Deletes still image or video files.

        :param str file_uri: ID of the file to delete
        :rtype: dict
        """
        req = self.__execute('camera.delete', fileUri=file_uri)
        return req.json()


class ThetaError(Exception):
    """Theta Error"""
    pass
