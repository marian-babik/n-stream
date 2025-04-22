import sys
import os.path
import argparse
import logging
import collections
import time

from messaging.queue.dqs import DQS

from nstream.structures import mq_event_factory
import nstream
import nstream.config
import nstream.settings

log = logging.getLogger('nstream')
# log.addHandler(logging.NullHandler()) needs py2.7+


def main():
    parser = argparse.ArgumentParser(description='Reads messages/events from directory queue and '
                                                 'submits them to ElasticSearch')
    parser.add_argument('--config', '-c', default='/etc/nagios-mq/nstream.cfg',
                        help="Configuration file (default %s)." % '/etc/nagios-mq/nstream.cfg')
    parser.add_argument('--debug', '-d', action='store_true',
                        help="Enables debug output sent to a log file")
    parser.add_argument('--log', '-l', default='/var/log/nstream.log',
                        help="Path to the log file (use keyword stdout for console)")
    parser.add_argument('-t', dest='timeout', default=nstream.settings.PLUGIN_TIMEOUT,
                        help="Timeout for plugin execution (default %s)." % nstream.settings.PLUGIN_TIMEOUT)
    args = parser.parse_args()

    if args.debug:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s %(module)s: %(message)s')
    if args.log == 'stdout':
        fh = logging.StreamHandler(stream=sys.stdout)
    else:
        fh = logging.FileHandler(args.log)
    fh.setFormatter(formatter)
    log.addHandler(fh)

    log.info("---------------------------------")
    log.info("nstream version {}".format(nstream.VERSION))
    log.info("---------------------------------")

    config = nstream.config.load_stream_config(cf=args.config)
    if not config:
        log.error("Unable to load configuration file %s" % args.config)
        sys.exit(2)

    for handler in config.keys():
        if not isinstance(config[handler], collections.Mapping):
            continue
        backend = config[handler].get('backend')
        dirq = config[handler].get('dirq', None)
        args = config[handler].get('args', None)

        if not backend:
            log.error("No backend found in the config, exiting")
            sys.exit(2)

        # sanity
        if not os.path.exists(dirq) or not dirq:
            log.error("Directory queue missing or unreadable (%s)" % dirq)
            sys.exit(2)

        # check ES config

        # todo: load backend
        try:
            # change to importlib.import_module for 2.7+
            b_mod = __import__("nstream.backends.%s" % backend, None, None, [backend])
        except ImportError as e:
            log.exception(e)
            sys.exit(2)

        # dirq processing
        while True:
            count = 0
            events = list()
            try:
                mq = DQS(path=dirq)
            except Exception as e:
                log.exception(e)
                sys.exit(2)

            for entry in mq:
                if mq.lock(entry):
                    try:
                        # get event from mq
                        event = mq_event_factory(mq, entry)

                        # filter
                        if config[handler].get('filter', None):
                            event = config[handler].get('filter')(event)
                            if not event:
                                mq.unlock(entry)
                                continue

                        events.append(event)
                        count += 1
                    except Exception as e:
                        mq.unlock(entry)
                        log.exception(e)
                        sys.exit(2)
                    else:
                        # mq.unlock(entry)
                        mq.remove(entry)
                else:
                    log.warning("Unable to acquire lock for %s" % entry)
            # call
            b_mod.insert(events, **args)
            log.info("Processed %d messages" % count)
            time.sleep(config[handler].get('timeout', 10))
