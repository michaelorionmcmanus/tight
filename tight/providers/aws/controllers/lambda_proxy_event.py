# Copyright (c) 2017 lululemon athletica Canada inc.
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

import sys
import importlib
import json
import traceback
import datetime
from functools import partial
from tight.core.structured_logger import log
from structlog.threadlocal import (
    bind_threadlocal,
)

methods = [
    'get', 'post', 'patch', 'put', 'delete', 'options'
]


def merge_dicts(*dict_args):
    """
    Given any number of dicts, shallow copy and merge into a new dict,
    precedence goes to key value pairs in latter dicts.
    """
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result


class HttpExitException(Exception):
    def __init__(self, response_code, response):
        response['statusCode'] = response_code
        self.response = response


class LambdaProxyController():
    HEADERS = {
        'Access-Control-Allow-Origin': '*'
    }

    def __init__(self):
        self.methods = {}
        for method in methods:
            def function(method, func, *args, **kwargs):
                self = kwargs.pop('self')
                self.attach_handler(func)
                controller_name = getattr(func, '__module__').split('.')[-2]
                self.methods['{}:{}'.format(controller_name, method.upper())] = func
            setattr(self, method, partial(function, method, self=self))

    def attach_handler(self, func):
        module_path = getattr(func, '__module__')
        function_module = importlib.import_module(module_path)
        try:
            getattr(function_module, 'handler')
        except Exception as e:
            setattr(function_module, 'handler', self.run)

    def prepare_args(self, *args, **kwargs):
        event = args[1]
        context = args[2]
        if ('body' in event and event['body'] != None):
            try:
                event['body'] = json.loads(event['body'])
            except Exception as e:
                log.info(message='Could not json.loads ' + str(event['body']))
                event['body'] = {}
        try:
            principal_id = event['requestContext']['authorizer']['claims']['sub']
        except Exception as e:
            principal_id = None

        return {
            'event': event,
            'context': context,
            'principal_id': principal_id
        }

    def prepare_response(self, *args, **kwargs):
        if ('passthrough' in kwargs):
            return kwargs['passthrough']
        # Map return properties to the response.
        if ('body' not in kwargs):
            kwargs['body'] = {}
        elif (not isinstance(kwargs['body'], str)):
            kwargs['body'] = json.dumps(kwargs['body'])
        # Default response code is 200
        if ('statusCode' not in kwargs):
            kwargs['statusCode'] = 200
        # Response header needs to specify `Access-Control-Allow-Origin` in order
        # for CORS to function properly.
        if ('headers' not in kwargs):
            kwargs['headers'] = {}

        headers = merge_dicts(kwargs['headers'], self.HEADERS)
        kwargs['headers'] = headers
        # Ship it!
        return kwargs

    def exit_with_response(self, response_code, response):
        raise HttpExitException(response_code, response)

    def run(self, *args, **kwargs):
        controller_name = args[0]
        event = args[1]
        context = args[2]
        bind_threadlocal(
            function_name=('function_name' in context and str(context.function_name)) or 'LAMBDA_FUNCTION_NAME',
            function_version=('function_version' in context and str(context.function_version)) or 'FUNCTION_VERSION',
            request_id=('aws_request_id' in context and str(context.aws_request_id)) or 'AWS_REQUEST_ID',
            run_start_time=datetime.datetime.now()
        )
        method = event['httpMethod']
        method_name = ':'.join([controller_name, method])
        log.info(f'RUN_{method_name}')
        method_handler = self.methods[':'.join([controller_name, method])]
        method_handler_args = self.prepare_args(*args, **kwargs)
        try:
            method_response = method_handler(*args, **method_handler_args)
        except HttpExitException as http_exit_instance:
            method_response = http_exit_instance.response
        except Exception as e:
            method_response = e
            trace_lines = traceback.format_exc()
        if type(method_response) is dict:
            prepared_response = self.prepare_response(**method_response)
        else:
            log.error('TIGHT_APP_FAILURE', exception=trace_lines, lambda_event=event, lambda_context=context)
            raise Exception('TIGHT_APP_FAILURE')
        return prepared_response


LambdaProxySingleton = LambdaProxyController()

current_module = sys.modules[__name__]


def expose():
    exit_with_response = getattr(LambdaProxySingleton, 'exit_with_response')
    setattr(current_module, 'exit_with_response', exit_with_response)
    for method in methods:
        handler = getattr(LambdaProxySingleton, method)
        setattr(current_module, method, handler)


expose()


def set_default_headers(headers):
    LambdaProxySingleton.HEADERS = headers


def handler(*args, **kwargs):
    """ Proxy to LambdaProxySingleton::run

    :param args:
    :param kwargs:
    :return: LambdaProxyController
    """
    return LambdaProxySingleton.run(*args, **kwargs)
