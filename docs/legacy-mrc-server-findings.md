# Uploaded Mystic Relay Chat Server v1.1 — offline compatibility notes

The uploaded `mrc_server.py` is a Python 2 TCP server, not a modern authenticated public relay.

## Observed protocol behavior

- Client first sends raw `site~platform/system/architecture/version` identification.
- Server `poll_clients()` emits `SERVER~~~CLIENT~~~ping~\n`.
- Client `IMALIVE:site` control traffic records a BBS site in `sites_by_sockets`.
- `IAMHERE` is a seven-field packet addressed to `SERVER`; the server
  records the sender's current room in `rooms_by_user` and site in
  `bbs_by_user`.
- `NEWROOM:old:new` updates the user's room; `LOGOFF` removes it.
- Non-server-directed chat packets are broadcast to all connected sockets;
  each client must filter its own room.
- Commands include `LIST`, `WHOON`, `USERS`, `CHANNEL`,
  `CHATTERS`, `CONNECTED`, `MOTD`, and `VERSION`.

## Known limitations in the uploaded server

- Python 2 `print` statements and `dict.iteritems()` require migration.
- `recv()` chunks are split by `os.linesep` without TCP reassembly; a
  packet can arrive fragmented or concatenated.
- `rooms_by_user` is keyed only by username, so duplicate handles from
  different sites can collide.
- Broad exception handlers hide protocol and socket errors.
- No authentication, TLS, or permissions model is evident in this source.
- The second address argument is parsed from the command line but not used
  for federation in the supplied code.

## BubbaBot implementation

The local-only runner now optionally sends `IAMHERE` after a server
heartbeat; the legacy-compatible raw identification remains restricted to
offline tests. Existing sessions that do not opt into presence are unchanged.

Do not deploy this legacy server or the simulated client publicly. We still
need explicit relay permission, supported identity details, and valid TLS
before live integration.
