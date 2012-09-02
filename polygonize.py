#!/usr/bin/python2
# -*- coding: utf-8 -*-
from xml.dom import minidom
from itertools import chain, cycle
from shapely.geometry import Polygon, MultiPolygon
import re

def ntuples(seq, n):
	l = len(seq)
	for i in xrange(l//n):
		yield seq[n*i: n*i+n]

def quadraticPatch(x0, y0, x1, y1, x2, y2, subdivisions=10):
	subdivisions += 1
	polyline = list()
	for i in range(1, subdivisions):
		t, u = float(i) / subdivisions, float(subdivisions-i) / subdivisions
		x = u*(u*x0 + t*x1) + t*(u*x1 + t*x2)
		y = u*(u*y0 + t*y1) + t*(u*y1 + t*y2)
		polyline.append((x, y))
	return polyline

# Supported commands
commands = 'mMlLqQtThHvVzZ' # that means, CARSDEFGJ are unsupported (in both variants)

pat_command = re.compile("([{}])([0-9-\.,\s]*)".format(commands))
pat_float = re.compile("[-+]?[0-9]*\.?[0-9]+")

def readsvg(filename):
	doc = minidom.parse(filename)
	paths = doc.getElementsByTagName("path")
	polygons = list()
	for path in paths:
		data = path.getAttribute("d")
		polygon = list()
		lastpoint = (0, 0)
		for cmd, argstring in re.findall(pat_command, data):
			if cmd in 'mlqtz':
				args = [float(s) + lastpoint[i] for s, i in zip(re.findall(pat_float, argstring), cycle((0,1)))]
				cmd = cmd.upper()
			else:
				args = [float(s) for s in re.findall(pat_float, argstring)]
			if cmd == 'T':
				# convert to a generic Q format
				points = iter(ntuples(args, 2))
				args = list()
				a = next(points)
				args.extend(a)
				for b in points:
					args.extend(((a[0]+b[0])/2, (a[1]+b[1])/2))
					args.extend(b)
					a = b
				cmd = 'Q'
			if cmd == 'Q' and len(args) == 2:
				cmd = 'L'
			if cmd in 'MLQhHvV':
				if cmd in 'ML':
					for x, y in ntuples(args, 2):
						lastpoint = (x, y)
				elif cmd == 'h':
					for x in args:
						lastpoint = (lastpoint[0] + x, lastpoint[1])
				elif cmd == 'H':
					for x in args:
						lastpoint = (x, lastpoint[1])
				elif cmd == 'v':
					for y in args:
						lastpoint = (lastpoint[0], lastpoint[1] + y)
				elif cmd == 'V':
					for y in args:
						lastpoint = (lastpoint[0], y)
				elif cmd == 'Q':
					for x1, y1, x2, y2 in ntuples(args, 4):
						polygon.extend(quadraticPatch(lastpoint[0], lastpoint[1], x1, y1, x2, y2))
						lastpoint = (x2, y2)
				polygon.append(lastpoint)
			elif cmd == 'Z':
				polygons.append(polygon)
				polygon = list()
		if polygon:
			polys.append(polygon)
	return MultiPolygon([Polygon(polygon) for polygon in polygons])
	
	#path.setAttribute("d", "M " + " Z\nM ".join(" L ".join("{:.4f}, {:.4f}".format(x, y) for x, y in poly) for poly in polys))
	#with open("polygonized.svg", "w+") as f:
	#	f.write(doc.toprettyxml())
	
