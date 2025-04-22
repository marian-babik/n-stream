import logging
import sys

import nstream.settings

log = logging.getLogger("nstream")


def insert(event, nagios_pipe=None):
    cmd_line = event.get('cmd', 'UNDEFINED')
    try:
        with open(nagios_pipe, 'w') as cmd_pipe:
            cmd_pipe.write(cmd_line)
    except Exception as e:
        log.error("Exception caught while writing to pipe (%s)" % (cmd_line))
        if nstream.settings.DEBUG:
            log.exception(e)
        sys.exit(2)

