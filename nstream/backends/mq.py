import logging
import json
import datetime
import copy
import re
import os

from nstream.structures import Event
import nstream.settings

from messaging.message import Message
from messaging.queue.dqs import DQS

log = logging.getLogger("nstream")


def insert(event, dirq=None, destination=None, c_map=None, m_map=None):

    mq_header = {'nagiosHost': event['serviceserver'],
                 'destination': destination}

    if m_map and 'servicedesc' in event.keys():
        for m_old in m_map.keys():
            if m_old in event['servicedesc']:
                event['servicedesc'] = event['servicedesc'].replace(m_old, m_map[m_old])

    # SAM3 summary limit is 256 chars
    if 'serviceoutput' in event.keys() and len(event['serviceoutput']) > 256:
        event['serviceoutput'] = event['serviceoutput'][:255]

    # RAW input processing
    if 'longserviceoutput' in event.keys() and '### Full plugin output' in event['longserviceoutput']:
        match = re.search(r'href=[\'"]?([^\'" >]+)', event['longserviceoutput'])
        if match:
            with open(os.path.join(nstream.settings.PLUGIN_RAW_OUTPUT_PREFIX, match.group(1).lstrip('/')), 'r') as rpo:
                event['longserviceoutput'] = rpo.read().replace('\n', '\\n')

    if c_map:
        m_event = Event()
        for k in event.keys():
            if k in c_map.keys():
                m_event[c_map[k]] = event[k]
        if 'timestamp' in m_event.keys():
            utc_ts = datetime.datetime.utcfromtimestamp(int(m_event['timestamp']))
            m_event['timestamp'] = utc_ts.strftime('%Y-%m-%dT%H:%M:%SZ')
        if 'serviceFlavour' in m_event.keys() and len(m_event['serviceFlavour'].split()) > 1:
            for sf in m_event['serviceFlavour'].strip().split():
                n_event = copy.copy(m_event)
                n_event['serviceFlavour'] = sf
                mq_body = json.dumps(dict(n_event))
                enqueue(dirq, mq_body, mq_header)
        else:
            mq_body = json.dumps(dict(m_event))
            enqueue(dirq, mq_body, mq_header)
    else:
        mq_body = json.dumps(dict(event))
        enqueue(dirq, mq_body, mq_header)


def enqueue(dirq, mq_body, mq_header):
    msg = Message(body=mq_body, header=mq_header)
    msg.is_text = True
    mq = DQS(path=dirq)
    mq.add_message(msg)
