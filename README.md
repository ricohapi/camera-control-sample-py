# Ricoh Camera Control Sample for Python

Camera Remote Control Python Library samples for Ricoh API.
You can send/receive a shoot message and parameters.

## Requirements

You need

* Ricoh API Client Credentials (client_id & client_secret)
* Ricoh ID (user_id & password)

If you don't have them, please register yourself and your client from [THETA Developers Website](http://contest.theta360.com/).

## Install

```sh
pip install --upgrade git+https://github.com/ricohapi/auth-py.git
pip install --upgrade git+https://github.com/ricohapi/media-storage-py.git
git clone https://github.com/ricohapi/camera-control-sample-py.git
```

In your downloaded directory,
```sh
pip install .
```

### Download Intermediate CA Certificate

This library uses MQTTS as the communication protocol.
You need a CA certificate to use MQTTS.
Download it from the URL below.
  https://support.comodo.com/index.php?/Knowledgebase/Article/GetAttachment/991/1070566


# Camera control samples
##Command-line sample
This is a command-line sample program of sending/receiving camera control messages.

### Setup
- Move to samples directory.
- Rename `config_template.json` to `config.json` and setup your credentials.

```json
{
  "USER": "set_your_user_id",
  "PASS": "set_your_user_pass",
  "CLIENT_ID": "set_your_client_id",
  "CLIENT_SECRET": "set_your_client_secret",
  "CA_CERTS": "path to the ca certificate files"
}
```

### Message Receiver Side

- Connect the host machine with the THETA S via Wi-Fi.
  For the details of Wi-Fi setup, refer to the URL below.
  - https://theta360.com/en/support/manual/s/content/prepare/prepare_06.html
- Connect the host machine to the Internet.
- Start listening to the camera control message to the `DEVID` device by running the command below.
- Once a message is received, the specified callback function is called.
  - Sender-specified device ID, command name, command parameters are passed along with the receiver-specified arguments.

```sh
$ python remocon.py --dev=DEVID start
```
You can specify your own `DEVID`.  It should be in a format `/[A-Za-z0-9_]{1,32}/`.

### Message Sender Side

- Connect the host machine to the Internet.
- Send a message to the `DEVID` device by running the command below.
- User parameters can be specified as a string.
  User parameter keys need to start with an underscore.
  This sample program expects JSON String formatted user parameters.

```sh
$ python remocon.py --dev=DEVID shoot

$ python remocon.py -DEVID -p'{"_shutterSpeed": 0.01, "_iso": 200}' shoot
```

### Example

On one terminal (device side)
```sh
$ python remocon.py --dev=DEV001 start

connecting...
hit enter key to quit.
```

On another (control side)
```sh
$ python remocon.py --dev=DEV01 shoot

$ python remocon.py -dDEV001 -p'{"_shutterSpeed": 0.01, "_iso": 200}' shoot
```

Then on the terminal (device side)
```sh
device   : DEV001
command  : shoot
message:  None
fun_param: callback_args
(take picture)

device   : DEV001
command  : shoot
rcv_param: {u'_shutterSpeed': 0.01, u'_iso': 200}
fun_param: callback_args
(take picture)
```

For details of the callback function, refer to the sample code `remocon.py`.



##Use sample API

These are camera control message receiver and sender samples using the Python SDK.


### Receiving a camera control message

```python
from ricohapi.cameractl.client import Client

with Client(client_id, client_secret) as camera:
    camera.connect(user_id, user_pass, ca_certs)
    camera.listen(dev_id, func=on_receive, fargs=('callback_args',))
    print('connecting...')
    print('hit enter key to quit.')
    _ = input()


def on_receive(devid, cmd, rcv_param, fun_param):
    '''Called back when a camera control message is received. '''
    print('device   :', devid)
    print('command  :', cmd)
    print('rcv_param:', rcv_param)
    print('fun_param:', fun_param)
    print('take picture')

```

### Sending a shooting message

```python
from ricohapi.cameractl.client import Client

with Client(client_id, client_secret) as camera:
    camera.connect(user_id, user_pass, ca_certs)
    camera.shoot(dev_id)

```




# Sample SDK API Usage
### Constructor

Put your Ricoh API Client ID and Client Secret.

```python
from ricohapi.cameractl.client import Client

camera = Client(client_id, client_secret)
```

### Connect to the server

Connect to the remote VCP server provided by Ricoh.
You'll need Ricoh User ID and Password, and also specify the path to the CA certificate.

```python
def connect(self, user_id, user_pass, ca_certs):
    """connect to the server.

    :param str user_id: your user id
    :param str user_pass: your password
    :param str ca_certs: The path to the ca certificate file.
    """
```

### Disconnect from the server

```python
def disconnect(self):
```

### Start listening to messages

Start listening to the camera control message to the device specified by the `device_id`.  
The device_id must be in a format `/[A-Za-z0-9_]{1,32}/`.  
The `func` and `fargs` are a callback function and its arguments which will be called when the message received.

The callback function is called with the target `device_id`, command name, command parameters, and the arguments specified via `fargs`.

If `func` is omitted, no callback call is triggered.

Refer to the sample code for more details.

```python
def listen(self, device_id, func=None, fargs=None):
    """Start listening to the camera control messages
       and callbacks when the message is received.

    :param str device_id: device id to which you want to send message.
    :param function func: callback function which called message is received
    :param tuple fargs: func argument
    """
```

ex.)
```sh
camera.listen(DEV_ID, func=on_receive, fargs=None)
```

### Terminate listening to messages

Terminate listening to the camera control message to the device specified by the `device_id`.

```python
def unlisten(self):
    """Unlisten to the camera control message that is already listened.
    """
```

### Send a shooting message

Send a shooting message to the device specified by the `device_id`.
You can specify a set of user parameters via the argument `param`.
The user parameters can include objects that are serializable by `msgpack-python`.
For details of `msgpack-python`, refer to the documentation below.
- https://pypi.python.org/pypi/msgpack-python

User parameters are passed to the receiver.

User parameters needs to be dictionary-formatted, and the key needs to start with an underscore (`_`).

For more details, refer to the sample code.

```python
def shoot(self, device_id, param=None):
    """Send a shooting message to the device specified by the device_id.

    :param str device_id: a device id to which you want to send message.
    :param dict param: user specified camera control parameters.
    """
```

ex.)
```sh
camera.shoot("dev001", '{"_shutterSpeed": 0.01, "_iso": 200}')
```
