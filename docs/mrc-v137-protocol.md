# MRC v1.3.7 protocol observations (offline reference)

Source: user-provided Phenom Productions `mrc_client(1).py`, v1.3.7, and Mystic MPL source. These are observations about that client, **not** proof of the live server's current policy.

1. The client connects via TCP or SSL and immediately sends raw bytes `bbsname~MYSTIC/<OS>/<architecture>/1.3.7` without a newline.
2. It then sends BBS information fields `INFOWEB`, `INFOTEL`, `INFOSSH`, `INFOSYS`, `INFODSC`, followed by `IMALIVE:<bbsname>` and `CAPABILITIES:MCI CTCP SSL`.
3. Subsequent control messages are seven tilde-delimited fields, with optional trailing tilde, typically ending in newline.
4. Server `PING` elicits `CLIENT~<bbsname>~<pid>~SERVER~~~IMALIVE:<bbsname>~\n`.
5. The client periodically requests `STATS` and sends `SHUTDOWN` on orderly exit.
6. The client loops over nonblocking socket reads. It does not implement a robust line reassembly protocol; BubbaBot should do so independently.

**Important:** The reference client's identification and capability values describe Mystic BBS, not a standalone bot. BubbaBot must not impersonate a Mystic installation or claim unsupported capabilities. The `mrc_handshake.py` functions are offline reference encoders only. Before any live connection, obtain operator permission, approved bot identity/rooms, current handshake and authorization details, TLS expectations, and acceptable heartbeat cadence. Never send production credentials or network traffic from the offline tests.
