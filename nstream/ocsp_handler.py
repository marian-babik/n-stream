import sys
import argparse
import logging
import collections

from nstream.structures import env_event_factory
import nstream.config
import nstream.settings

log = logging.getLogger('nstream')


# log.addHandler(logging.NullHandler()) needs py2.7+
class NullHandler(logging.Handler):
    def emit(self, record):
        pass


def main():
    parser = argparse.ArgumentParser(description='Nagios event handler to process OCSP events and add them to '
                                                 'a directory/message queue')
    parser.add_argument('--config', default='/etc/nstream/nstream.cfg',
                        help="Configuration file (default %s)." % '/etc/nstream/nstream.cfg')
    parser.add_argument('--debug', '-d', action='store_true',
                        help="Enables debug output sent to a log file")
    parser.add_argument('--log', '-l', default='/var/log/nstream.log',
                        help="Path to the log file (use keyword stdout for console)")
    args = parser.parse_args()
    debug = args.debug

    if debug:
        log.setLevel(logging.DEBUG)
        nstream.settings.DEBUG = True
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
        fh = NullHandler()
        log.addHandler(fh)

    config = nstream.config.load_stream_config(cf=args.config)
    if not config:
        log.error("Unable to load configuration file %s" % args.config)
        sys.exit(2)

    for handler in config.keys():
        if not isinstance(config[handler], collections.Mapping):
            continue
        backend = config[handler].get('backend')
        nagios_vars = config[handler].get('nagios_vars')
        args = config[handler].get('args', dict())
        if not backend or not args:
            log.error("No handler found or no arguments in the config, exiting")
            sys.exit(2)

        if nagios_vars:
            nagios_vars = ['NAGIOS_'+at.strip().upper() for at in nagios_vars]

        # get event from environment
        event = env_event_factory(nagios_vars)

        # filter
        try:
            if config[handler].get('filter', None):
                config[handler].get('filter')(event)
        except:
            log.debug("Exception while calling filter")
            e = sys.exc_info()[0]
            log.exception(e)
            sys.exit(2)

        # load backend
        try:
            # change to importlib.import_module for 2.7+
            b_mod = __import__("nstream.backends.%s" % backend, None, None, [backend])
        except ImportError as e:
            log.debug("Exception while importing backend")
            log.exception(e)
            sys.exit(2)
        except:
            log.debug("Exception while importing backend")
            e = sys.exc_info()[0]
            log.exception(e)
            sys.exit(2)

        # call backend
        try:
            b_mod.insert(event, **args)
        except Exception as e:
            log.debug("Exception while calling backend")
            log.exception(e)
            sys.exit(2)

