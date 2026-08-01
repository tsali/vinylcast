#!/usr/bin/env python3
"""vinylcast — silence-aware turntable -> Icecast controller.

MONITOR: read the Bluetooth turntable (A2DP), wait for real audio (peak above
         a threshold).
PUSH   : (optional intro clip, then) stream the turntable to the Icecast LIVE
         mount, all through ONE ffmpeg connection so the speakers never drop.
         When SILENCE_SEC of continuous silence is seen, stop -> Icecast falls
         back to whatever you've configured as the fallback source on that mount
         (or silence). Then it goes back to monitoring.

Config comes from environment variables (see config.env.example).

MIT License — Copyright (c) 2026 tsali
"""
import subprocess, sys, time, signal, array, os

BT_MAC      = os.environ.get("BT_MAC", "")
ALSA_PCM    = "bluealsa:DEV=%s,PROFILE=a2dp" % BT_MAC
RATE        = int(os.environ.get("SAMPLE_RATE", "48000"))
SILENCE_SEC = int(os.environ.get("SILENCE_SEC", "15"))
THRESH_DB   = os.environ.get("SILENCE_THRESH_DB", "-40dB")
INTRO_RAW   = os.environ.get("INTRO_RAW", "").strip()

ICE_PORT = os.environ.get("ICECAST_PORT", "8005")
ICE_PW   = os.environ.get("ICECAST_SOURCE_PW", "")
MOUNT    = os.environ.get("LIVE_MOUNT", "live").lstrip("/")
ICE_LIVE = "icecast://source:%s@localhost:%s/%s" % (ICE_PW, ICE_PORT, MOUNT)

# Peak amplitude (16-bit) that counts as "playing". -40 dBFS ~= 328.
THRESH_AMP = int(32768 * (10 ** (float(THRESH_DB.replace("dB", "")) / 20.0)))


def log(m):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), m), flush=True)


def arecord():
    return subprocess.Popen(
        ["arecord", "-D", ALSA_PCM, "-f", "S16_LE", "-r", str(RATE),
         "-c", "2", "-t", "raw", "-q"],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)


def monitor_state():
    """Block until real audio is detected on the turntable. False if capture dies."""
    arec = arecord()
    chunk = int(RATE * 2 * 2 * 0.3)  # ~300ms of S16_LE stereo
    try:
        while True:
            data = arec.stdout.read(chunk)
            if not data or len(data) < chunk:
                return False  # BT dropped / capture ended
            a = array.array("h")
            a.frombytes(data)
            if a and max(abs(x) for x in a) > THRESH_AMP:
                return True
    finally:
        try:
            arec.kill()
        except Exception:
            pass


def push_state():
    """Stream turntable -> Icecast LIVE until SILENCE_SEC of silence, then return."""
    if INTRO_RAW and os.path.isfile(INTRO_RAW):
        feed_cmd = "cat %s; exec arecord -D '%s' -f S16_LE -r %d -c 2 -t raw -q" % (
            INTRO_RAW, ALSA_PCM, RATE)
    else:
        feed_cmd = "exec arecord -D '%s' -f S16_LE -r %d -c 2 -t raw -q" % (ALSA_PCM, RATE)
    feed = subprocess.Popen(["bash", "-c", feed_cmd],
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    ff = subprocess.Popen(
        ["ffmpeg", "-hide_banner", "-loglevel", "info",
         "-f", "s16le", "-ar", str(RATE), "-ac", "2", "-i", "-",
         "-af", "silencedetect=n=%s:d=%d" % (THRESH_DB, SILENCE_SEC),
         "-c:a", "libmp3lame", "-ar", "44100", "-ac", "2", "-b:a", "192k",
         "-map", "0:a", "-f", "mp3", ICE_LIVE],
        stdin=feed.stdout, stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE, text=True)
    feed.stdout.close()
    try:
        for line in ff.stderr:
            if "silence_start" in line:
                return
    finally:
        for p in (ff, feed):
            try:
                p.terminate()
            except Exception:
                pass
        time.sleep(0.3)
        for p in (ff, feed):
            try:
                p.kill()
            except Exception:
                pass


def main():
    if not BT_MAC:
        log("ERROR: BT_MAC not set (see config.env). Exiting.")
        sys.exit(1)
    intro = "yes" if (INTRO_RAW and os.path.isfile(INTRO_RAW)) else "none"
    log("vinylcast controller up (intro=%s); mount=/%s; silence=%ds" % (intro, MOUNT, SILENCE_SEC))
    while True:
        if not monitor_state():
            time.sleep(2)
            continue
        log("sound detected -> streaming turntable to /%s" % MOUNT)
        push_state()
        log("%ds silence -> stopped (mount falls back)" % SILENCE_SEC)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, lambda *a: sys.exit(0))
    main()
