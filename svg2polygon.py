#!/usr/bin/python2
# -*- coding: utf-8 -*-
from xml.dom import minidom
from itertools import cycle
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

def cubicPatch(x0, y0, x1, y1, x2, y2, x3, y3, subdivisions=10):
    subdivisions += 1
    polyline = list()
    for i in range(1, subdivisions):
        t, u = float(i) / subdivisions, float(subdivisions-i) / subdivisions
        x = u*(u**2 * x0 + 3*t*(u*x1 + t*x2)) + t**3*x3
        y = u*(u**2 * y0 + 3*t*(u*y1 + t*y2)) + t**3*y3
        polyline.append((x, y))
    return polyline


def svg_to_shapely(**kwargs):
    """ Calls svg_to_lists and converts the data to Shapely Polygon objects.

    Subpaths are treated as polygon interiors, i. e. they create a hole inside of the bigger polygon.
    """
    shapely_polygon = None
    for polygon in [Polygon(polygon) for polygon in svg_to_lists(**kwargs) if (len(polygon)>2)]:
        if not shapely_polygon:
            shapely_polygon = polygon
        else:
            shapely_polygon = shapely_polygon.symmetric_difference(polygon)
            # TODO if MultiPolygon is created, extend the output Multipolygon
            #       if Polygon is created, append it to the output Multipolygon
            #print type(shapely_polygon)
    #outpolys = [Polygon(polygon) for polygon in polygons if (len(polygon)>2)]
    #return MultiPolygon(outpolys)
    return shapely_polygon

def svg_to_lists(filename, xs=1, ys=1):
    """ Reads all path objects from a SVG, interpolates all Bézier curves. Returns the polygon as list of (x,y) tuples. 

    Does not handle any other SVG objects than paths. May not handle all SVG formats.

    This version does not handle paths and subpaths differently.
    """ 
    # Supported commands
    commands = 'mMlLqQtThHvVzZcC' # that means, ARSDEFGJ are unsupported (in both variants)
    pat_command = re.compile("([{}])([0-9-\.,\s]*)".format(commands))
    pat_float = re.compile("[-+]?[0-9]*\.?[0-9]+")

    doc = minidom.parse(filename)
    paths = doc.getElementsByTagName("path")
    polygons = list()
    for path in paths:
        data = path.getAttribute("d")
        polygon = list()
        lastpoint = (0, 0)
        for cmd, argstring in re.findall(pat_command, data):
            if cmd in 'mlqtzc':
                # convert relative to absolute coordinates
                args = [(float(s) + lastpoint[index]) * scale for s, scale, index in zip(re.findall(pat_float, argstring), cycle((xs, ys)), cycle((0,1)))]
                cmd = cmd.upper()
            else:
                args = [float(s) * scale for s, scale in zip(re.findall(pat_float, argstring), cycle((xs, ys)))]
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
            if cmd in 'MLQhHvVcC':
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
                elif cmd == 'C':
                    for x1, y1, x2, y2, x3, y3  in ntuples(args, 6):
                        polygon.extend(cubicPatch(lastpoint[0], lastpoint[1], x1, y1, x2, y2, x3, y3))
                        lastpoint = (x3, y3)
                polygon.append(lastpoint)
            elif cmd == 'Z':
                ## adding subpath of a path
                polygons.append(polygon)
                polygon = list()
        if polygon:
            ## adding a path
            polygons.append(polygon)
    return polygons
    
    #path.setAttribute("d", "M " + " Z\nM ".join(" L ".join("{:.4f}, {:.4f}".format(x, y) for x, y in poly) for poly in polys))
    #with open("polygonized.svg", "w+") as f:
    #    f.write(doc.toprettyxml())
