import os
from pythonjsonlogger import jsonlogger
import datetime
import logging, sys
from structlog import wrap_logger
import structlog
from structlog.threadlocal import (
    merge_threadlocal,
)

root = logging.getLogger()
if root.handlers:
    for handler in root.handlers:
        root.removeHandler(handler)


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        log_record['level'] = record.levelname


formatter = CustomJsonFormatter('(message)')
logging.basicConfig(format='%(message)s', level=('LOG_LEVEL' in os.environ and os.environ['LOG_LEVEL']) or logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(formatter)
root_logger = logging.getLogger()
root_logger.addHandler(handler)


def censor_password(_, __, event_dict):
    pw = event_dict.get("password")
    if pw:
        event_dict["password"] = "*CENSORED*"
    return event_dict


def add_timestamp(_, __, event_dict):
    event_dict["now"] = datetime.datetime.now()
    return event_dict


log = wrap_logger(
    root,
    processors=[
        censor_password,
        merge_threadlocal,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        add_timestamp,
        structlog.processors.TimeStamper(),
        structlog.stdlib.render_to_log_kwargs,
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

root.propagate = False


def get_logger():
    return log
