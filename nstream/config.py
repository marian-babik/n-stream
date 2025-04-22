import os
import sys
import logging

import nstream.settings

log = logging.getLogger("nstream")


def load_stream_config(cf='/etc/nstream/nstream.cfg'):
    stream_config = dict()
    if not os.path.exists(cf):
        if nstream.settings.DEBUG:
            logging.error("Default config path access error (%s)" % cf)
        sys.exit(2)

    try:
        with open(cf) as f:
            code = compile(f.read(), os.path.basename(cf), 'exec')
            exec(code, {}, stream_config)
    except Exception as e:
        if nstream.settings.DEBUG:
            logging.exception(e)
        sys.exit(2)
    return stream_config


