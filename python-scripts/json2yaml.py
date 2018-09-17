#!/usr/bin/env python

import simplejson as json
import yaml
import argparse

parser = argparse.ArgumentParser(description='Convert a JSON file to YAML')
parser.add_argument('filename', help='a JSON file to parse')
parser.add_argument('--output', dest='outfile', help='Filename to write to (defaults to stdout)')

args = parser.parse_args()

infile = open(args.filename, 'r')
jsondata = json.load(infile)
infile.close()

yamldata = yaml.dump(jsondata, allow_unicode=True, default_flow_style=False)

if args.outfile:
	out = open(args.outfile, 'w')
	out.write(yaml_data)
	out.close
else:
	print yamldata

exit(0)
