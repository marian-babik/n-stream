import logging
import sys
import time

import nstream.settings

log = logging.getLogger("nstream")


def insert(event, nagios_pipe=None):
    timestamp = event.get('lastservicecheck', time.time())
    hostname = event.get('hostname', 'UNDEFINED')
    service = event.get('servicedesc', 'UNDEFINED')
    status = event.get('servicestate', 'UNDEFINED')
    output = event.get('serviceoutput', 'UNDEFINED')
    cmd_line = "[%d] PROCESS_SERVICE_CHECK_RESULT;%s;%s;%s;%s\n" % (timestamp, hostname, service, status, output)
    try:
        with open(nagios_pipe, 'w') as cmd_pipe:
            cmd_pipe.write(cmd_line)
    except Exception as e:
        log.error("Exception caught while writing to pipe (%s, %s)" % (hostname, service))
        if nstream.settings.DEBUG:
            log.exception(e)
        sys.exit(2)
