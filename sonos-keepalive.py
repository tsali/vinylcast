#!/usr/bin/env python3
"""vinylcast — keep a Sonos speaker pinned to the local Icecast LIVE stream.

Sonos (and most network speakers) will STOP an internet-radio stream after any
hiccup and won't auto-resume. This polls the speaker; if it's STOPPED/idle it
re-points it at the local LIVE mount and hits Play — so the speaker is always
sitting on the stream and your audio comes through the instant it starts.

Only acts when STOPPED/idle, so it won't fight you if you're playing something
else on that speaker.

For a Sonos STEREO PAIR, set SPEAKER_IP to the COORDINATOR's IP.

Config comes from environment variables (see config.env.example).

MIT License — Copyright (c) 2026 tsali
"""
import urllib.request, re, time, os

SPEAKER = os.environ.get("SPEAKER_IP", "")
PI_IP   = os.environ.get("PI_IP", "")
PORT    = os.environ.get("ICECAST_PORT", "8005")
MOUNT   = os.environ.get("LIVE_MOUNT", "live").lstrip("/")
POLL    = int(os.environ.get("KEEPALIVE_POLL_SEC", "5"))

# Sonos needs the x-rincon-mp3radio:// scheme (a bare http:// URI throws UPnP 714).
LIVE = "x-rincon-mp3radio://%s:%s/%s" % (PI_IP, PORT, MOUNT)


def soap(action, inner):
    ep = "http://%s:1400/MediaRenderer/AVTransport/Control" % SPEAKER
    body = ('<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" '
            's:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"><s:Body>'
            '<u:%s xmlns:u="urn:schemas-upnp-org:service:AVTransport:1">%s</u:%s>'
            '</s:Body></s:Envelope>') % (action, inner, action)
    req = urllib.request.Request(ep, data=body.encode(), headers={
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": '"urn:schemas-upnp-org:service:AVTransport:1#%s"' % action,
    })
    return urllib.request.urlopen(req, timeout=8).read().decode()


def main():
    if not SPEAKER or not PI_IP:
        print("ERROR: SPEAKER_IP and PI_IP must be set (see config.env).", flush=True)
        raise SystemExit(1)
    print("vinylcast keepalive up -> speaker %s, stream %s (every %ds)" % (SPEAKER, LIVE, POLL), flush=True)
    while True:
        try:
            ti = soap("GetTransportInfo", "<InstanceID>0</InstanceID>")
            m = re.search(r"<CurrentTransportState>([^<]+)<", ti)
            state = m.group(1) if m else ""
            if state in ("STOPPED", "PAUSED_PLAYBACK", "NO_MEDIA_PRESENT"):
                soap("SetAVTransportURI",
                     "<InstanceID>0</InstanceID><CurrentURI>%s</CurrentURI>"
                     "<CurrentURIMetaData></CurrentURIMetaData>" % LIVE)
                soap("Play", "<InstanceID>0</InstanceID><Speed>1</Speed>")
        except Exception:
            pass
        time.sleep(POLL)


if __name__ == "__main__":
    main()
