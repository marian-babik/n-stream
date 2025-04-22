import time
import os
import logging

from elasticsearch import Elasticsearch, exceptions as es_exceptions
from elasticsearch import helpers

log = logging.getLogger("nstream")


def flush(bulk_dataset):
    success = False
    while not success:
        success = bulk_index(bulk_dataset)
        if success:
            break
        else:
            log.error("Unable to post to ES")
            time.sleep(10)


def bulk_index(data):
    """
    sends the data to ES for indexing.
    if successful returns True.
    """
    success = False
    global ES_CONN
    if not ES_CONN:
        ES_CONN = get_es_connection()
    try:
        res = helpers.bulk(ES_CONN, data, raise_on_exception=True, request_timeout=120)
        log.info("inserted:", res[0], 'errors:', res[1])
        success = True
    except es_exceptions.ConnectionError as error:
        log.exception(error)
    except es_exceptions.TransportError as error:
        log.exception(error)
    except helpers.BulkIndexError as error:
        log.exception(error)
    except Exception as e:
        log.exception(e)
        # Reset the ES connection
        ES_CONN = None
    return success


def get_es_connection():
    """
    establishes es connection.
    """
    log.debug("make sure we are connected to ES...")
    while True:
        try:
            es_host = None
            http_auth = None
            if 'ES_HOST' in os.environ:
                es_host = os.environ["ES_HOST"]
            else:
                es_host = "http://ps-collection.atlas-ml.org"

            if 'ES_USER' in os.environ and 'ES_PASS' in os.environ:
                http_auth = (os.environ['ES_USER'], os.environ['ES_PASS'])
                es_conn = Elasticsearch([es_host], http_auth=http_auth)
            else:
                es_conn = Elasticsearch([es_host])
            log.debug("connected OK!")
        except es_exceptions.ConnectionError as error:
            log.exception(error)
        except Exception as e:
            log.exception(e)
        else:
            return es_conn
        time.sleep(70)


ES_CONN = get_es_connection()
