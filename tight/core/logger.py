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

import logging
import os
import datetime
import sys
import calendar
import structlog
# from structlog import wrap_logger
# from structlog.processors import JSONRenderer
# from structlog.stdlib import filter_by_level
#
# logging.basicConfig(
#     stream=sys.stdout,
#     format="%(message)s",
#     level=('LOG_LEVEL' in os.environ and os.environ['LOG_LEVEL']) or logging.INFO
# )
#
#
# def add_timestamp(_, __, event_dict):
#     dt = datetime.datetime.utcnow()
#     event_dict["timestamp"] = calendar.timegm(dt.utctimetuple())
#     return event_dict
#
#
# def censor_password(_, __, event_dict):
#     pw = event_dict.get("password")
#     if pw:
#         event_dict["password"] = "*CENSORED*"
#     return event_dict
#
#
# processors = [
#     structlog.stdlib.filter_by_level,  # First step, filter by level to
#     structlog.stdlib.add_logger_name,  # module name
#     structlog.stdlib.add_log_level,  # log level
#     structlog.stdlib.PositionalArgumentsFormatter(),  # % formatting
#     structlog.processors.StackInfoRenderer(),  # adds stack if stack_info=True
#     structlog.processors.format_exc_info,  # Formats exc_info
#     structlog.processors.UnicodeDecoder(),  # Decodes all bytes in dict to unicode
#     structlog.processors.TimeStamper(),  # Because timestamps! UTC by default
# ]
#
# # Configure structlog
# structlog.configure(
#     processors=processors,
#     context_class=dict,
#     logger_factory=structlog.stdlib.LoggerFactory(),
#     wrapper_class=structlog.stdlib.BoundLogger,
#     cache_logger_on_first_use=True,
# )
#
# structured_logger = structlog.get_logger()

def info(*args, **kwargs):
    """
    Log a message using the system logger.

    :param args:
    :param kwargs:
    :return: None
    """
    message = kwargs.pop('message')


def error(*args, **kwargs):
    message = kwargs.pop('message')


def warn(*args, **kwargs):
    message = kwargs.pop('message')
