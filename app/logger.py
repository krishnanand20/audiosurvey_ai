import logging
from contextlib import contextmanager

import colorlog

handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    "%(log_color)s[%(levelname)s] %(message)s",
    log_colors={
        'DEBUG':    'cyan',
        'INFO':     'green',
        'WARNING':  'yellow',
        'ERROR':    'red',
        'CRITICAL': 'bold_red',
    }
))

logger = colorlog.getLogger("audiosurvey")
logger.propagate = False

if not logger.handlers:
    logger.addHandler(handler)

logger.setLevel(logging.INFO)

NOISY_LOGGER_NAMES = (
    "httpx",
    "httpcore",
    "httpcore.connection",
    "httpcore.http2",
    "hpack",
    "hpack.hpack",
    "h2",
    "h2.connection",
    "h2.config",
    "gtts",
    "gtts.tts",
    "googletrans",
    "urllib3",
    "torio",
    "torio._extension",
    "torio._extension.utils",
    "torchaudio",
)

for noisy_name in NOISY_LOGGER_NAMES:
    logging.getLogger(noisy_name).setLevel(logging.WARNING)

werkzeug_logger = logging.getLogger("werkzeug")
werkzeug_logger.setLevel(logging.INFO)


@contextmanager
def silence_noisy_library_logs():
    saved = []
    for noisy_name in NOISY_LOGGER_NAMES:
        lib_logger = logging.getLogger(noisy_name)
        saved.append(
            (
                lib_logger,
                lib_logger.level,
                lib_logger.propagate,
                lib_logger.disabled,
            )
        )
        lib_logger.setLevel(logging.CRITICAL)
        lib_logger.propagate = False
        lib_logger.disabled = True
    try:
        yield
    finally:
        for lib_logger, level, propagate, disabled in saved:
            lib_logger.setLevel(level)
            lib_logger.propagate = propagate
            lib_logger.disabled = disabled
