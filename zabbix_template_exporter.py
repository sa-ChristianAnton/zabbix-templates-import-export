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
import xml.dom.minidom

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
    parser.add_argument('-D', '--directory', type=str, default='.', help='directory to dump template files to')
    parser.add_argument('-n', '--name', type=str, required=False, help='technical name of template to export')
    parser.add_argument('-v', '--visible-name', type=str, required=False, help='visible name of the template to export')
    parser.add_argument('-t', '--tarball', action='store_true', help='create tarball of all exported templates in given directory')
    parser.add_argument('-r', '--reset-date', action='store_true', help='reset export date to 2000-01-01T00:00:00Z')
    parser.add_argument('-j', '--json', action='store_true', help='format of output')
    # parser.add_argument('somearg', type=str, default='bla', help='this is something important')
    args = parser.parse_args()
    if args.debug:
        loglevel = logging.DEBUG
    return args

def main():
    if args.tarball:
        tmp_dir = tempfile.mkdtemp()
    today = datetime.date.today().strftime('%Y-%m-%d')

    zapi = ZabbixAPI(os.environ['ZABBIX_URL'], user=os.environ['ZABBIX_USERNAME'], password=os.environ['ZABBIX_PASSWORD'])

    if args.json:
        export_format='json'
    else:
        export_format='xml'

    if args.name:
        templates = zapi.template.get(filter={'host': args.name})
    elif args.visible_name:
        templates = zapi.template.get(filter={'name': args.visible_name})
    else:
        templates = zapi.template.get()

    for template in templates:
        logging.info('found template "%s" (%s) with id %s' % (template['name'], template['host'], template['templateid']))
        #template_file_basename = re.sub(r'[ \.]', '_', template['name'])
        template_file_basename = re.sub(r'\/', '#', template['host'])
            
        if args.tarball:
            backup_file_path = os.path.join(tmp_dir, '%s.%s' % (template_file_basename, export_format))
        else:
            backup_file_path = os.path.join(args.directory, '%s.%s' % (template_file_basename, export_format))

        f = open(backup_file_path, 'w')

        template_output = zapi.configuration.export(format=export_format, options={'templates': [template['templateid']]})
        if args.json:
            j = json.loads(template_output)
            if args.reset_date:
                j['zabbix_export']['date'] = '2000-01-01T00:00:00Z'
            f.write(json.dumps(j, sort_keys=True, indent=4))
        else:
            dom = xml.dom.minidom.parseString(template_output)
            if args.reset_date:
                date = dom.firstChild.getElementsByTagName('date')
                date[0].firstChild.data = '2000-01-01T00:00:00Z'
            pretty_xml_as_string = dom.toprettyxml(indent="  ")
            f.write(pretty_xml_as_string)

    if len(templates) == 0:
        raise Exception('no templates found')

    if args.tarball:
        logging.info('creating tarball in %s' % args.directory)
        tarfile_path = os.path.join(args.directory, 'templates_%s.tar.gz' % today)
        tar = tarfile.open(tarfile_path, 'w:gz')
        tar.add(tmp_dir, arcname='')
        tar.close()
        shutil.rmtree(tmp_dir)


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
