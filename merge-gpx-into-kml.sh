#!/bin/bash

gpsbabel -i gpx -o kml,points=0 $(for GPX in *.gpx; do echo -n " -f $GPX "; done) -x simplify,error=0.01K -F map.kml
