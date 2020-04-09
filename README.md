# Zabbix Template importer / exporter

These two tools have been written in order to export and import Zabbix templates via Zabbix API

## General usage
Access to Zabbix API is controlled by setting the following environment variables:
* ZABBIX_URL
* ZABBIX_USERNAME
* ZABBIX_PASSWORD

Once these are set correctly, either the Zabbix Importer or Exporter can be used with the proper command line arguments.

## Exporter
The exporter exports either one specific template (by given name) or ALL templates from Zabbix and saves them in one file each. Every file is named exactly like the template inside Zabbix (slashes in template names are being substituted to "#" hashmarks) with a suffix same to the export format chosen (default: xml, json with the -j command line argument). The files are placed all within the same directory, which by default is the current working directory ("."). The export directory can be chosen with the -D switch. If tarball creation "-t" is chosen, all exports are being done into a temp directory instead, and only a tarball with the current date and time within the file name is being placed inside the export directory. This is for pure backup scenarios.
For better tracking of template changes in git, it is possible to override the date field in each of the export files to one single and always same date string. This has been implemented in order not to generate DIFFs in git if the exact same template is being checked in again (no changes). Without overriding the export date field, a change would be recognized every time.

### Parameters
* `-d`, `--debug`: set log messages to DEBUG level
* `-D`, `--directory`: directory to dump template files or tarball to, defaults to "."
* `-n`, `--name`: name of the template to export, if not set, ALL templates are being exported
* `-t`, `--tarball`: instead of placing every found template into the directory one by one, create one tarball of all templates exported
* `-r`, `--reset-date`: reset the export date inside the xml/json files to the fixed value of "2000-01-01T00:00:00Z" for easier tracking in git
* `-j`, `--json`: use JSON export format instead of XML

### Examples
Export all templates of a Zabbix installation into /tmp directory as one tarball containing all of them. All xml files will have the export overridden to "2000-01-01T00:00:00Z":
  python3 zabbix_template_exporter.py -r -D /tmp/

Export one specific template into current working directory, in JSON format
  python3 zabbix_template_exporter.py -n "my special template" -j


## Importer
The importer is meant to read either an XML or JSON file containing either one or more templates and import these into Zabbix via API. Files being exported by the formerly explained Exporter within this project can be used as input files.
The "import options" are not yet configurable within this importer. They are hard coded and set to the most "hard" way of overriding everything possible inside Zabbix, so please take care and use diff before blindly overriding things in your Zabbix installation.

### Parameters
* `-d`, `--debug`: set log messages to DEBUG level
* `-f`, `--file`: file to read and import (can bei either XML or JSON format, please note the `-j` parameter as well)
* `-j`, `--json`: read fil in JSON format instead of XML. Please note, there is currently no automatic detection of the input format, so make sure to use the right combination of input data format and the `-j` parameter

### Examples
Import single XML file:
  python3 zabbix_template_importer.py -j "my nice template.xml"