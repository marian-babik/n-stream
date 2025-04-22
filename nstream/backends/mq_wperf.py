import logging
import json
import datetime
import copy
import re

from nstream.structures import Event

from messaging.message import Message
from messaging.queue.dqs import DQS

log = logging.getLogger("nstream")

TOKENIZER_RE = (
    r"([^\s]+|'[^']+')=([-.\d]+)(c|s|ms|us|B|KB|MB|GB|TB|%)?" +
    r"(?:;([-.\d]+))?(?:;([-.\d]+))?(?:;([-.\d]+))?(?:;([-.\d]+))?")


def _normalize_to_unit(value, unit):
    if unit == 'ms':
        return value / 1000.0
    if unit == 'us':
        return value / 1000000.0
    if unit == 'KB':
        return value * 1024
    if unit == 'MB':
        return value * 1024 * 1024
    if unit == 'GB':
        return value * 1024 * 1024 * 1024
    if unit == 'TB':
        return value * 1024 * 1024 * 1024 * 1024

    return value


def parse_perfdata(s):
    metrics = dict()
    counters = re.findall(TOKENIZER_RE, s)
    if counters is None:
        log.warning("Failed to parse performance data: {s}".format(s=s))
        return metrics

    for (key, value, uom, warn, crit, min, max) in counters:
        try:
            norm_value = _normalize_to_unit(float(value), uom)
            metrics[key] = norm_value
        except ValueError:
            log.warning("Couldn't convert value '{value}' to float".format(value=value))

    return metrics


def insert(event, dirq=None, destination=None, c_map=None, m_map=None):

    mq_header = {'nagiosHost': event['serviceserver'],
                 'destination': destination}
    if m_map and 'servicedesc' in event.keys():
        for m_old in m_map.keys():
            if m_old in event['servicedesc']:
                event['servicedesc'] = event['servicedesc'].replace(m_old, m_map[m_old])
    if c_map:
        m_event = Event()
        for k in event.keys():
            if k in c_map.keys():
                m_event[c_map[k]] = event[k]
        if 'timestamp' in m_event.keys():
            utc_ts = datetime.datetime.utcfromtimestamp(int(m_event['timestamp']))
            m_event['datetime'] = utc_ts.strftime('%Y-%m-%dT%H:%M:%SZ')
        if 'perfdata' in m_event.keys():
            metrics = parse_perfdata(m_event['perfdata'])
            m_event['perf_metrics'] = metrics
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
