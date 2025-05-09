#!/usr/bin/env python

import logging
import copy

import nstream.logstash_api

log = logging.getLogger("nstream")


def convert_to_float(d, tags):
    for t in tags:
        if t not in d:
            continue
        v = d[t]
        if not v:
            continue
        if isinstance(v, float):
            continue
        d[t] = float(v)


def convert_to_int(d, tags):
    for t in tags:
        if t not in d:
            continue
        v = d[t]
        if not v:
            continue
        if isinstance(v, int):
            continue
        if v.isdigit():
            d[t] = int(v)
        else:
            d[t] = None


def fix_enabled(services):
    for d in services:
        for k, v in d.items():
            if k == "enabled" and v in ["1", "true", "True"]:
                d[k] = 1
            if k == "enabled" and v in ["0", "false", "False"]:
                d[k] = 0


def isfloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


def clean(data):
    to_del = []
    for tag in data.keys():
        if data[tag] is None or data[tag] == 'unknown':
            to_del.append(tag)
        if type(data[tag]) is dict:
            clean(data[tag])
    for tag in to_del:
        del data[tag]


def insert(events):
    bulk_dataset = list()
    for m in events:
        data = dict()

        data['type'] = 'meta'
        data.update(m)
        data.pop('interfaces', None)
        data['timestamp'] = int(float(m['timestamp']) * 1000)
        data['ps_host'] = data.get('external_address', {}).get('dns_name')

        if 'services' in data.keys():
            fix_enabled(data['services'])
        if "services" in data:
            sers = copy.deepcopy(data["services"])
            data["services"] = {}
            for s in sers:
                if "name" in s:
                    service_name = s["name"]
                    del s["name"]
                    tps = {}
                    if "testing_ports" in s:
                        for tp in s["testing_ports"]:
                            if 'type' not in tp:
                                continue
                            tps[tp['type']] = {"min_port": tp["min_port"],
                                               "max_port": tp["max_port"]}
                        s['testing_ports'] = tps
                    data["services"][service_name] = s
                else:
                    continue

        clean(data)

        if 'location' in data.keys():
            lat = data['location'].get('latitude', 0)
            lgt = data['location'].get('longitude', 0)
            if lat and lgt and isinstance(lat, str) and isinstance(lgt, str):
                if isfloat(lat) and isfloat(lgt):
                    data['geolocation'] = "%s,%s" % (lat, lgt)
            del data['location']

        if 'ntp' in data.keys():
            n = data['ntp']
            convert_to_float(n, ['delay', 'dispersion', 'offset'])
            convert_to_int(n, ['synchronized', 'stratum', 'reach', 'polling_interval'])

        if 'external_address' in data.keys():
            ea = data['external_address']
            if 'counters' in ea.keys():
                convert_to_int(ea['counters'], ea['counters'].keys())

        convert_to_int(data, ['cpu_cores', 'cpus'])
        convert_to_float(data, ['cpu_speed'])
        bulk_dataset.append(data)
    nstream.logstash_api.flush(bulk_dataset)


