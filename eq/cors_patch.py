#!/usr/bin/env python3
# Idempotently add a global CORS header to Icecast so a cross-origin page can read /live.
import sys
F = "/etc/icecast2/icecast.xml"
s = open(F).read()
if "Access-Control-Allow-Origin" in s:
    print("CORS header already present — no change"); sys.exit(0)
block = ('    <http-headers>\n'
         '        <header name="Access-Control-Allow-Origin" value="*" />\n'
         '    </http-headers>\n')
if "</icecast>" not in s:
    print("ERROR: </icecast> not found"); sys.exit(1)
s = s.replace("</icecast>", block + "</icecast>", 1)
open(F, "w").write(s)
print("CORS header added to icecast.xml")
