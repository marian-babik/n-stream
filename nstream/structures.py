import logging
import os
import sys
import socket
import collections
import json
from builtins import str

import nstream.settings

log = logging.getLogger('nstream')


def env_event_factory(attr=None):
    event = Event()
    # populate
    for k in os.environ.keys():
        if 'NAGIOS_' not in k:
            continue
        # ignore soft states
        #if k == 'NAGIOS_SERVICESTATETYPE' and os.environ[k] == "SOFT":
        #    log.debug("Ignoring a soft state event")
        #    sys.exit(2)
        ev_key = k[7:].lower()
        if attr and k in attr:
            event[ev_key] = os.environ[k]
        else:
            event[ev_key] = os.environ[k]

    # empty event
    if not event and nstream.settings.DEBUG:
        log.debug("Empty event detected, please check if environment is populated by Nagios")
        sys.exit(2)

    if nstream.settings.DEBUG:
        log.debug("Event (%s, %s): %s" % (event['hostname'], event['servicedesc'],
                                          len(list(event.keys()))))

    # sanity for long service output (long output has hard-coded limit of 8kB)
    #if 'longserviceoutput' in event.keys() \
    #        and len(event['longserviceoutput']) > nstream.settings.PLUGIN_OUTPUT_LIMIT:
    #    event['longserviceoutput'] = event['longserviceoutput'][
    #                                       0:nstream.settings.PLUGIN_OUTPUT_LIMIT - 5] + ' ...'

    # transformations
    if 'longserviceoutput' in event.keys():
        event['longserviceoutput'] = str(event['longserviceoutput'], 'utf8', errors='replace')
    if 'serviceserver' not in event.keys():
        event['serviceserver'] = socket.gethostname()

    return event


def mq_event_factory(mq, entry):
    event = Event()
    q_msg = mq.get_message(entry)
    msg = json.loads(q_msg.get_body())
    msg['header'] = q_msg.get_header()
    event.update(msg)
    return event


def cmd_event_factory(mq, entry):
    event = Event()
    event['cmd'] = mq.get_message(entry).get_body()
    return event


class Event(collections.MutableMapping):
    def __init__(self, *args, **kwargs):
        self.store = dict()
        self._debug = nstream.settings.DEBUG
        self.update(dict(*args, **kwargs))  # use the free update to set keys

    def __contains__(self, x):
        return x in self.store.keys()

    def __getitem__(self, key):
        return self.store[key]

    def __setitem__(self, key, value):
        self.store[key] = value

    def __delitem__(self, key):
        del self.store[key]

    def __iter__(self):
        return iter(self.store)

    def __len__(self):
        return len(self.store)
