import time
import socket
import json
import os
import logging
import requests

log = logging.getLogger("nstream")


def flush(bulk_dataset):
    success = False
    while not success:
        success = bulk_index(bulk_dataset)
        if success:
            break
        else:
            log.error("Unable to post to Logstash, retrying in 60 seconds ...")
            time.sleep(60)


def bulk_index(data):
    """
    sends the data to Logstash HTTP plugin for indexing.
    if successful returns True.
    """
    counter = 0
    if 'LS_URI' in os.environ:
        ls_uri = os.environ["LS_URI"]
    else:
        ls_uri = "http://ps-collection.atlas-ml.org"

    try:
        headers = {"content-type": "application/json"}
        with requests.Session() as s:
            for entry in data:
                log.debug(json.dumps(entry))
                s.put(ls_uri, headers=headers, data=json.dumps(entry))
                counter += 1
                # This is sample code for same functionality with Logstash TCP plugin
                # with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                #     sock.connect((ls_host, ls_port))
                #     for entry in data:
                #         sock.sendall(json.dumps(entry).encode('utf-8'))
                #         sock.send(b'\n')
    except socket.error as msg:
        log.exception(msg)
        return False
    except Exception as e:
        log.exception(e)
        return False

    log.info("{} messages sent to logstash".format(counter))
    return True


