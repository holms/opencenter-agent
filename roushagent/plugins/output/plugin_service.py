#!/usr/bin/env python
# 
# Copyright 2012, Rackspace US, Inc. 
# 
# Licensed under the Apache License, Version 2.0 (the "License"); 
# you may not use this file except in compliance with the License. 
# You may obtain a copy of the License at 
# 
#     http://www.apache.org/licenses/LICENSE-2.0 
# 
# Unless required by applicable law or agreed to in writing, software 
# distributed under the License is distributed on an "AS IS" BASIS, 
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. 
# See the License for the specific language governing permissions and 
# limitations under the License. 
# 

import os
import subprocess
import sys
import time

name = 'service'


def setup(config={}):
    LOG.debug('Setting up service "service"')

    register_action('service_start', service_action)
    register_action('service_stop', service_action)
    register_action('service_restart', service_action)


def service_action(input_data):
    payload = input_data['payload']
    action = input_data['action']

    full_restart = False
    sleep = 0

    if not 'service' in payload:
        return _return(1, 'no "service" in payload')

    if 'sleep' in payload:
        sleep = payload['sleep']

    service = payload['service']
    service_action = action.split('_')[1]
    command = ['service', service, service_action]

    LOG.debug('preparing to run service command: "%s"' % (' ').join(command))

    result = subprocess.call(command, shell=False)

    if sleep:
        time.sleep(int(sleep))

    return _return(result, os.strerror(result))


def _return(result_code, result_str, result_data=None):
    if result_data is None:
        result_data = {}
    return {'result_code': result_code,
            'result_str': result_str,
            'result_data': result_data}


def _success(result_str='success', result_data=None):
    if result_data is None:
        result_data = {}
    return _return(0, result_str, result_data)
