import logging
import sys
import uuid
from contextvars import ContextVar

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get()
        return True


def setup_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | request_id=%(request_id)s | %(name)s | %(message)s"
    )
    handler.setFormatter(formatter)
    handler.addFilter(RequestIdFilter())

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers = [handler]


def new_request_id() -> str:
    return str(uuid.uuid4())[:8]
