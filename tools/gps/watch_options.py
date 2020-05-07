"WATCH options - controls what data is streamed, and how it's converted"
WATCH_ENABLE = 0x000001        # enable streaming
WATCH_DISABLE = 0x000002       # disable watching
WATCH_JSON = 0x000010          # JSON output
WATCH_NMEA = 0x000020          # output in NMEA
WATCH_RARE = 0x000040          # output of packets in hex
WATCH_RAW = 0x000080           # output of raw packets

WATCH_SCALED = 0x000100        # scale output to floats
WATCH_TIMING = 0x000200        # timing information
WATCH_DEVICE = 0x000800        # watch specific device
WATCH_SPLIT24 = 0x001000       # split AIS Type 24s
WATCH_PPS = 0x002000           # enable PPS JSON

WATCH_NEWSTYLE = 0x010000      # force JSON streaming
WATCH_OLDSTYLE = 0x020000      # force old-style streaming
