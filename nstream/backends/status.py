import logging

import nstream.logstash_api

log = logging.getLogger("nstream")


def insert(events):
    bulk_dataset = list()
    for m in events:
        data = dict()

        metrics = ['perfSONAR services: ntp', 'perfSONAR esmond freshness',
                   'perfSONAR services: pscheduler']
        found = False
        for met in metrics:
            if met not in m['metric']:
                continue
            found = True
        if not found:
            continue

        if 'perf_metrics' in m.keys() and not m['perf_metrics']:
            continue

        data['type'] = 'status'
        data['ps_host'] = m['host']
        prefix = m['metric'].replace("perfSONAR", "ps").replace(":", "").replace(" ", "_").lower()
        for k in m['perf_metrics'].keys():
            data[prefix + "_" + k] = m['perf_metrics'][k]
        data['timestamp'] = int(float(m['timestamp']) * 1000)
        bulk_dataset.append(data)
    nstream.logstash_api.flush(bulk_dataset)
