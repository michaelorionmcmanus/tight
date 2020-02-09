import os
from pythonjsonlogger import jsonlogger
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

logging.basicConfig(format='%(message)s', level=('LOG_LEVEL' in os.environ and os.environ['LOG_LEVEL']) or logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(jsonlogger.JsonFormatter())
root_logger = logging.getLogger()
root_logger.propagate = False
root_logger.addHandler(handler)


def censor_password(_, __, event_dict):
    pw = event_dict.get("password")
    if pw:
        event_dict["password"] = "*CENSORED*"
    return event_dict


log = wrap_logger(
    logging.getLogger(__name__),
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
        structlog.processors.TimeStamper(),
        structlog.stdlib.render_to_log_kwargs,
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)


def get_logger():
    return log
