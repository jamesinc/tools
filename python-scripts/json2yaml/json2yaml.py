#!/usr/bin/env python

# This script ingests a JSON file and ultimately spits out a YAML file
# You can optionally define a transforms file (in JSON) that describes custom mappings between the input and output objects, including calculated outputs

# If a move operation contains an array, we need to iterate every item in that array and apply the move operation to it

import json
import jmespath
import yaml
import argparse

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def _decode_list(data):
	rv = []
	for item in data:
		if isinstance(item, unicode):
			item = item.encode('utf-8')
		elif isinstance(item, list):
			item = _decode_list(item)
		elif isinstance(item, dict):
			item = _decode_dict(item)
		rv.append(item)
	return rv

def _decode_dict(data):
	rv = {}
	for key, value in data.iteritems():
		if isinstance(key, unicode):
			key = key.encode('utf-8')
		if isinstance(value, unicode):
			value = value.encode('utf-8')
		elif isinstance(value, list):
			value = _decode_list(value)
		elif isinstance(value, dict):
			value = _decode_dict(value)
		rv[key] = value
	return rv


def merge(source, destination):
	"""Deep-merge objects"""
	for key, value in source.items():
		if isinstance(value, dict):
			# get node or create one
			node = destination.setdefault(key, {})
			merge(value, node)
		else:
			destination[key] = value

	return destination

def create( ds, value ):
	"""Create a datastructure based on the given JMESPath definition"""
	ds = ds.split( "." )
	result = value
	# Reverse the namespace so we can iteratively wrap our object with more object
	for key in reversed(ds):
		print "PARSING FOR " + key
		is_array = key.find("[]", -2) >= 0

		new_result = [ ] if is_array else { }
		new_result[key.strip("[]")] = [ result ] if is_array else result
		result = new_result

	return result


def copy( source, mapping ):
	"""Copy a datastructure from one point to another (in a larger structure)"""
	value = jmespath.search(mapping["source"], source)

	if value:
		source = merge(create(mapping["target"], value), source)
	else:
		print "Unable to find path " + mapping["source"]
		
	return source


def move( haystack, needle, strawberry, start=False ):
	"""
		Finds a needle in a haystack, and then puts the needle inside a strawberry (another position in the haystack)
		If the haystack contains any lists, hoo boy you are in for a real humdinger, as this badboy will try and figure
		it all out. The only limitation is that the needles and strawberries need to be in the same lists (i.e. you can't move
		the needle to a strawberry in another list).

		The function will go into each item in the list, and start its lookup process again from that point.
	"""

	if start:
		if needle == strawberry:
			print "%sSource and destination are the same - nothing to do [%s]%s" % (bcolors.WARNING, needle, bcolors.ENDC)
			return haystack
		else :
			print "Moving [%s%s%s] => [%s%s%s]" % (bcolors.OKGREEN, needle, bcolors.ENDC, bcolors.OKGREEN, strawberry, bcolors.ENDC)

		needle = needle.translate(None, "[]").split(".")
		strawberry = strawberry.translate(None, "[]").split(".")

	# 1. Find the needle
	if len(needle) > 1:
		if isinstance(haystack[needle[0]], list):
			print "%s-- Found a list at [%s]%s" % (bcolors.OKBLUE, needle[0], bcolors.ENDC)
			# Reset the needle and strawberry to be relative to the list item
			print "-- Starting an iterative process to move [%s] to [%s]" % (".".join(needle[1:]), ".".join(strawberry[1:]))
			return [ move(hay, needle[1:], strawberry[1:]) for hay in haystack[needle[0]] ]
		else:
			print "%s-- Found an object at [%s]%s" % (bcolors.OKBLUE, needle[0], bcolors.ENDC)
			return move(haystack[needle[0]], needle[1:], strawberry)
	else:
		print "%s-- Found the needle: %s%s" % (bcolors.WARNING, needle, bcolors.ENDC)
		print "   \__ %s" % str(haystack[needle[0]])
		print "%s-- Moving the needle to [%s]%s" % ( bcolors.WARNING, ".".join(strawberry), bcolors.ENDC )
		# Copy the needley boi and return it
		# return { needle[0]: haystack[needle[0]] }
		# We've found the needle
		# 2. Take the needle and move it to strawberry, and then return the object
		# 2.1. Create the strawberry
		
		data_to_move = haystack[needle[0]]

		# Delete the original object (this is a move operation)
		del haystack[needle[0]]

		for pip in reversed(strawberry):

			data_to_move = { pip: data_to_move }

		print "   -- Wrapped output pre-merge: %s" % str(data_to_move)
		print "   -- Target: %s" % str(haystack)
		print "   -- Merged output: %s" % str(merge(data_to_move, haystack))

		return merge(data_to_move, haystack)


def transform( x, transforms ):

	# Move operations
	map(lambda op: move(x, op["source"], op["target"], True), transforms["move"])

	return x


parser = argparse.ArgumentParser(description='Convert a JSON file to YAML')
parser.add_argument('filename', help='a JSON file to parse')
parser.add_argument('--output', dest='outfile', help='Filename to write to (defaults to stdout)')
parser.add_argument('--transforms', dest='transformsfile', help='Transforms file to apply to the output YAML')
parser.add_argument('--debug', dest='debug', help='Debug output', default=False)

args = parser.parse_args()
debug = True if args.debug else False

infile = open(args.filename, 'r')
trsfile = open(args.transformsfile, 'r')

jsondata = json.load(infile, object_hook=_decode_dict)
jsontransforms = json.load(trsfile, object_hook=_decode_dict)

infile.close()
trsfile.close()

jsondata = transform( jsondata, jsontransforms )
yamldata = yaml.dump(jsondata, allow_unicode=True, default_flow_style=False)

if args.outfile:
	out = open(args.outfile, 'w')
	out.write(yamldata)
	out.close
else:
	print yamldata

exit(0)
