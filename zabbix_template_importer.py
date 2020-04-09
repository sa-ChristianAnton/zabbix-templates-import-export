#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Little program to export all Zabbix Templates either to to one tar.gz or to individual xml files'
"""
__description__ = 'Little program to export Zabbix Templates either to to one tar.gz or to individual xml files'
__author__     = "Christian Anton, secadm GmbH <christian.anton@secadm.de>"
__copyright__  = "Copyright 2017, secadm GmbH, Im Krautgarten 22, 82216 Maisach"
__license__    = "MIT"
__version__    = "0.1.0"
__maintainer__ = "Christian Anton"
__email__      = "christian.anton@secadm.de"
__status__     = "Production"


import os
import re
import tempfile
import tarfile
import datetime
import shutil
import sys
import logging
import argparse
import json

from zabbix.api import ZabbixAPI

loglevel = logging.WARNING


def set_up_logging(loglevel, log_to_foreground, program_name=None):
    if log_to_foreground is True:
        logging.basicConfig(level=loglevel, format='%(levelname)s:%(message)s')

    else:
        # logging.basicConfig(level=loglevel, format='%(asctime)s %(levelname)s:%(message)s')
        class ContextFilter(logging.Filter):
            hostname = socket.gethostname()
            username = pwd.getpwuid(os.getuid())[0]

            def filter(self, record):
                record.hostname = ContextFilter.hostname
                record.username = ContextFilter.username
                return True

        syslog_socket = "/dev/log"
        if 'darwin' == sys.platform:
            # Hint for macOS:
            # To configure syslog to writhe DEBUG messages to /var/log/system.log
            # - the agent must be started in daemon mode
            # - the agent must be started with debug option
            # - add the following line must be added to /etc/asl.conf:
            # ? [= Sender EdwardAgent] [<= Level debug] file system.log
            # - syslogd must be restarted
            syslog_socket = '/var/run/syslog'

        syslog_format_string = '[%(process)d]: [%(levelname)s][%(funcName)s] %(message)s'
        rootLogger = logging.getLogger()
        rootLogger.setLevel(loglevel)

        syslogFilter = ContextFilter()
        rootLogger.addFilter(syslogFilter)

        if program_name is None:
            program_name = os.path.basename(__file__)
        syslog = SysLogHandler(address=syslog_socket, facility=SysLogHandler.LOG_USER)
        syslogFormatter = logging.Formatter('%s %s' % (program_name, syslog_format_string), datefmt='%b %d %H:%M:%S')
        syslog.setFormatter(syslogFormatter)
        rootLogger.addHandler(syslog)


def parse_arguments():
    global loglevel
    parser = argparse.ArgumentParser(description=__description__)
    parser.add_argument('-d', '--debug', action='store_true', help='set log level to DEBUG')
    parser.add_argument('-f', '--file', type=str, help='file to load (xml/json)')
    parser.add_argument('-j', '--json', action='store_true', help='format of output')
    # parser.add_argument('somearg', type=str, default='bla', help='this is something important')
    args = parser.parse_args()
    if args.debug:
        loglevel = logging.DEBUG
    return args

def main():
    # read the file into a string
    try:
        file = open (args.file, "r")
        data=file.read()
    except Exception as e:
        raise e

    zapi = ZabbixAPI(os.environ['ZABBIX_URL'], user=os.environ['ZABBIX_USERNAME'], password=os.environ['ZABBIX_PASSWORD'])

    if args.json:
        import_format='json'
    else:
        import_format='xml'

    zapi.do_request(
        'configuration.import',
        {
            "format": import_format,
            "rules": {
                "applications": {
                    "createMissing": True,
                    "deleteMissing": True
                },
                "discoveryRules": {
                    "createMissing": True,
                    "updateExisting": True,
                    "deleteMissing": True
                },
                "graphs": {
                    "createMissing": True,
                    "updateExisting": True,
                    "deleteMissing": True
                },
                "groups": {
                    "createMissing": True
                },
                "hosts": {
                    "createMissing": True,
                    "updateExisting": True
                },
                "httptests": {
                    "createMissing": True,
                    "updateExisting": True,
                    "deleteMissing": True
                },
                "images": {
                    "createMissing": False,
                    "updateExisting": False
                },
                "items": {
                    "createMissing": True,
                    "updateExisting": True,
                    "deleteMissing": True
                },
                "maps": {
                    "createMissing": False,
                    "updateExisting": False
                },
                "screens": {
                    "createMissing": False,
                    "updateExisting": False
                },
                "templateLinkage": {
                    "createMissing": True,
                    # supported from 4.4? "deleteMissing": True
                },
                "templates": {
                    "createMissing": True,
                    "updateExisting": True
                },
                "templateScreens": {
                    "createMissing": True,
                    "updateExisting": True,
                    "deleteMissing": True
                },
                "triggers": {
                    "createMissing": True,
                    "updateExisting": True,
                    "deleteMissing": True
                },
                "valueMaps": {
                    "createMissing": True,
                    "updateExisting": True
                }
            },
            "source": data
        }
    )


if __name__ == '__main__':
    args = parse_arguments()
    log_to_foreground = False
    if sys.stdin.isatty():
        if int(loglevel) >= int(logging.INFO):
            loglevel = logging.INFO
        log_to_foreground = True
    set_up_logging(loglevel, log_to_foreground, program_name='zabbix_template_exporter')
    try:
        sys.exit(main())
    except Exception as e:
        logging.error(e)
        sys.exit(255)
