import configparser
import ipaddress
import os
import random
import requests
from dataclasses import dataclass
from functools import reduce
from hashlib import md5
from pprint import pformat

config_file = 'config.ini'
config = configparser.ConfigParser(defaults={
    'url': 'CHANGE TO API ENDPOINT',
    'email': 'CHANGE TO NTNU STUDENT MAIL',
    'phone': 'CHANGE TO PHONE NUMBER'
})
config.read('config.ini')

if not os.path.exists(config_file):
    with open(config_file, "w") as f:
        config.write(f)


@dataclass
class Session:
    """ Store a running session. """
    id: int = None
    user_id: int = None

# the session is stored globally so that it can be used in get and post methods
session = Session()


def jsonf(json):
    """ Pretty format a json dictionary. 
    
    :param json: a python dictionary
    :returns: formatted str
    """
    return pformat(json, indent=4)


def get(endpoint: str, in_session: bool=True):
    """ Request with HTTP GET and return json from the given API endpoint.

    :param endpoint: the API endpoint
    :param in_session: include the session in the request
    :returns: response json as a dict
    """
    url = config["DEFAULT"]["url"]
    print(f'requesting from {url + endpoint}')
    response = requests.get(url + endpoint, params={'sessionId': session.id} if in_session else {})
    response_json = response.json()

    print(f'response: {response}:\n{jsonf(response_json)}')
    return response_json


def post(endpoint: str, json: dict, in_session: bool=True):
    """ Send json with HTTP POST and return json from the given API endpoint.

    :param endpoint: the API endpoint
    :param json: dict to send as json
    :param in_session: include the session in the request
    :returns: response json as a dict
    """
    url = config["DEFAULT"]["url"]
    if in_session:
        json['sessionId'] = session.id

    print(f'sending to {url + endpoint}:\n{jsonf(json)}')
    response = requests.post(url + endpoint, json=json)
    response_json = response.json()
    
    print(f'response: {response}:\n{jsonf(response_json)}')
    return response_json


def authorize(email, phone):
    """ Authorize with email and phone number, and save the session.

    :param email: the email of the user
    :param phone: the phone number of the user
    """
    session_json = post('auth', {
        'email': email,
        'phone': phone
    }, in_session=False)

    if not session_json['success']:
        return
    
    # setup global session
    session.id = session_json["sessionId"]
    session.user_id = session_json["userId"]


def perform_task1():
    """ Send a static "Hello" message to the server. """
    get('gettask/1')
    post('solve', {'msg': 'Hello'})


def perform_task2():
    """ Echo back the message received. """
    json = get('gettask/2')
    msg = json['arguments'][0]
    post('solve', {'msg': msg})


def perform_task3():
    """ Multiply the arguments and send back the result. """
    json = get('gettask/3')

    # multiply all numbers in arguments
    numbers = map(int, json['arguments'])
    multiplied = reduce(lambda x, y: x * y, numbers)
    
    post('solve', {'result': multiplied})


def hash_code(code: int):
    """ Hash an integer in md5.

    :param code: integer to hash
    :returns: the md5 hashed code
    """
    return md5(str(code).encode(encoding='ascii')).hexdigest()


def perform_task4():
    """ Solve a password using an md5 hash. """
    json = get('gettask/4')
    hashed_code = json['arguments'][0]

    # find the hashed code
    for code in range(0, 10000):
        if hash_code(code) == hashed_code:
            break
    
    post('solve', {'pin': code})


def perform_secret():
    """ Find any valid ip in a given network and netmask. """
    json = get('gettask/2016')
    response_network = json['arguments'][0]
    response_netmask = json['arguments'][1]
    
    # create a network with the given netmask and find the first valid host
    network = ipaddress.ip_network(f'{response_network}/{response_netmask}')
    ip = next(network.hosts())

    post('solve', {'ip': str(ip)})


def main():
    # authorize user
    authorize(config["DEFAULT"]["email"], config["DEFAULT"]["phone"])

    # perform all tasks (any output is printed in get and post methods)
    perform_task1()
    perform_task2()
    perform_task3()
    perform_task4()
    perform_secret()

    # return the results
    get(f'results/{session.id}', in_session=False)


if __name__ == '__main__':
    main()
