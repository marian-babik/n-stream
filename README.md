**nstream** is a library written in Python to help stream data to and from Nagios core.

It has the following features:
* Supports Nagios core OCSP readout (via env. variables)
* Streaming to AMQ/RMQ (with stompclt)
* Streaming to Logstash or ElasticSearch
* Pluggable backend system with the following backends:
  * mq - send metrics to directory queue (dirq)
  * mq_wperf - send metrics including performance to directory queue
  * nagios - send metrics to nagios command pipe
  * nagios_cmd - send metrics to nagios command pipe (with command generation)
  
The following are sample configurations:
```shell
# This config will use ocsp_handler script to readout metrics 
# from nagios core, parse nagios_vars, map them to new attributes via c_map
# and store them as json files in a directory queue (dirq) via mq_wperf.
# Destination corresponding to a messaging topic/queue is added to each file.
# The directory queue can then be further processed by stompclt tool to publish
# messages to AMQ/RMQ 

# cat /etc/nstream/ocsp_handler.cfg
handler = { 'backend' : 'mq_wperf',
            'nagios_vars' : ('servicedesc', 'hostname', 'servicestate', 
                             'longserviceoutput', '_servicetags',
                             '_servicevo','_servicevo_fqan', 'serviceoutput',
                             '_servicetags', 'lastservicecheck', 'serviceperfdata'),
            'args' : { 'dirq' : '/var/spool/nstream/outgoing',
                       'c_map' : { 'servicedesc' : 'metric',
                                   'hostname' : 'host',
                                   'servicestate' : 'status',
                                   'longserviceoutput' : 'details',
                                   'serviceoutput' : 'summary',
                                   '_servicetags' : 'tags',
                                   'lastservicecheck' : 'timestamp',
                                   'serviceperfdata' : 'perfdata'
                                  },
                       'destination' : '/some/mq/topic',
                    },
         }

# This is how to integrate ocsp_handler script with Nagios core
# cat /etc/nagios.d/handlers.cfg         
#####
# OCSP commands
#####

define command {
        command_name handle_service_check
        command_line /usr/bin/ocsp_handler --config /etc/nstream/ocsp_handler.cfg
}

```

```commandline
# This config will use es_handler to readout metrics from nagios core
# filter out some of them based on some value of an attribute
# and send them to Logstash 

# cat /etc/nstream/elk.cfg 
def status_filter(event):
    if '<something>' in event['<attribute>']:
        return event

handler = { 'backend' : '<backend>',
            'filter': status_filter,
            'timeout': 60,
            'dirq' : '/var/spool/nstream/outgoing',
            'args' : {},
}
```
```python
# a simple <backend> for previous example would like something this:
import logging

import nstream.logstash_api

log = logging.getLogger("nstream")


def insert(events):
    bulk_dataset = list()
    for m in events:
        data = dict()
        data.update(m)
        data['timestamp'] = int(float(m['timestamp']) * 1000)
        bulk_dataset.append(data)
    nstream.logstash_api.flush(bulk_dataset)
```

Finally, mq_handler can be used to read metrics from a directory queue and submit it to the 
Nagios core via Nagios command pipe. Sample configuration would look somethign like this:
```shell
# cat /etc/nstream/mq_handler.cfg
def status_filter(event):
    if '<something>' in event['<attribute>']:
        return event

handler = { 'backend' : 'nagios_cmd',
            'filter': status_filter,
            'dirq' : '/var/spool/nstream/outgoing',
            'args' : { 'nagios_pipe': '/var/nagios/cmd'},
          }
```
