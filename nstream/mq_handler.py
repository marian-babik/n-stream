import sys
import os.path
import argparse
import logging
import collections

from messaging.queue.dqs import DQS

from nstream.structures import cmd_event_factory
import nstream.config
import nstream.settings

log = logging.getLogger('nstream')
# log.addHandler(logging.NullHandler()) needs py2.7+


def main():
    parser = argparse.ArgumentParser(description='Nagios plugin that reads messages/events from directory queue and '
                                                 'submits them to the Nagios command pipe')
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
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(module)s[%(process)d]: %(message)s')
        if args.log == 'stdout':
            if sys.version_info[0] == 2 and sys.version_info[1] <= 6:
                fh = logging.StreamHandler(strm=sys.stdout)
            else:
                fh = logging.StreamHandler(stream=sys.stdout)
        else:
            fh = logging.FileHandler(args.log)
        fh.setFormatter(formatter)
        log.addHandler(fh)
    else:
        log.setLevel(logging.NOTSET)
        # py2.7+
        #log.addHandler(logging.NullHandler())

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

        if not backend or not args:
            log.error("No handler found in the config or missing arguments, exiting")
            sys.exit(2)

        cmd_pipe = config[handler]['args'].get('nagios_pipe', None)

        # sanity
        if not os.path.exists(dirq) or not dirq:
            log.error("Directory queue missing or unreadable (%s)" % dirq)
            sys.exit(2)

        if not os.path.exists(cmd_pipe):
            log.error("Nagios command pipe unreadable (%s)" % cmd_pipe)
            sys.exit(2)

        # load backend
        try:
            # change to importlib.import_module for 2.7+
            b_mod = __import__("nstream.backends.%s" % backend, None, None, [backend])
        except ImportError as e:
            log.exception(e)
            sys.exit(2)

        # dirq processing
        count = 0
        try:
            mq = DQS(path=dirq)
        except Exception as e:
            log.exception(e)
            sys.exit(2)
        for entry in mq:
            if mq.lock(entry):
                try:
                    # get event from mq
                    event = cmd_event_factory(mq, entry)

                    # filter
                    if config[handler].get('filter', None):
                        event = config[handler].get('filter')(event)
                        if not event:
                            continue

                    # call
                    b_mod.insert(event, **args)
                    count += 1
                except Exception as e:
                    if args.debug:
                        log.exception(e)
                    sys.exit(2)
                finally:
                    mq.unlock(entry)
                    #mq.remove(entry)
            else:
                log.warning("Unable to acquire lock for %s" % entry)
        if args.debug:
            log.info("Processed %d messages" % count)
        sys.exit(0)
