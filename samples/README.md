# Command-line sample

This is a command-line sample program of sending/receiving camera control messages.

## Setup

Rename `config_template.json` to `config.json` and setup your credentials.

```json
{
  "USER": "set_your_user_id",
  "PASS": "set_your_user_pass",
  "CLIENT_ID": "set_your_client_id",
  "CLIENT_SECRET": "set_your_client_secret",
  "CA_CERTS": "path to the ca certificate files"
}
```

## Message Receiver Side

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

## Message Sender Side

- Connect the host machine to the Internet.
- Send a message to the `DEVID` device by running the command below.
- User parameters can be specified as a string.
  User parameter keys need to start with an underscore.
  This sample program expects JSON String formatted user parameters.

```sh
$ python remocon.py --dev=DEVID shoot

$ python remocon.py -DEVID -p'{"_shutterSpeed": 0.01, "_iso": 200}' shoot
```

## Example

For the details of the callback function, refer to the sample code.

On one terminal (device side)
```sh
$ python remocon.py --dev=DEV001 start

connecting...
hit enter key to quit.
```

On another (control side)
```sh
$ python remocon.py --dev=DEV01 shoot

$ python remocon.py -dDEV01 -p'{"_shutterSpeed": 0.01, "_iso": 200}' shoot
```

Then on the terminal (device side)
```sh
device   : DEV01
command  : shoot
message:  None
fun_param: callback_args
(take picture)

device   : DEV01
command  : shoot
rcv_param: {u'_shutterSpeed': 0.01, u'_iso': 200}
fun_param: callback_args
(take picture)
```

