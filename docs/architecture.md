# BubbaBot architecture and protocol notes

## Evidence from user's uploaded files

- `mrc_client(1).py` advertises MRC multiplexer v1.3.7. It sends outgoing messages from `data/mrc/*.mrc` and receives network messages, which it writes to active Mystic node queues.
- MRC packets observed in the client contain `from_user~from_site~from_room~to_user~to_site~to_room~message~`.
- `mrc_config.py` names `mrc.bottomlessabyss.net`, SSL port 5001, and SSL enabled.
- `startchat.cmd` appears configured for a Python 2 executable and a locally installed `mrc_client.py`, not necessarily the uploaded v1.3.7 copy. The actual runtime version requires verification.
- The historical `mrc_full.zip` includes an old `mrc_server.py`; do not assume it matches the live shared server.

## Target design

```text
Participating BBSes <---> Shared MRC server <---> BubbaBot MRC transport
                                                 |
                                                 v
                                        Packet + room router
                                                 |
                                                 v
                                     Abuse / rate / budget checks
                                                 |
                                                 v
                                           AI answer backend
```

The independent-client approach is **proposed**, not yet live validated. Server operators may restrict non-BBS clients, duplicate BBS identities, unsolicited bot messages, or room creation.

## Pending verification

1. Confirm the relay network permits a clearly labeled AI bot.
2. Confirm registration/handshake, username attribution, room identity and message routing.
3. Determine whether rooms are auto-created and how channels are joined.
4. Verify server response to reconnects and partial/multiple TCP frames; use buffered framing.
5. Confirm handling of direct messages, control messages, MCI color codes, and max packet/line lengths.
6. Avoid using Dave's BBS identity as a separate client unless operator permits it.
7. Configure host, TLS verification, key management, suppression rules and logging without exposing private conversations.

## Deployment guardrails

Default to offline mode. Never enable outbound networking merely by installing the project. Start with permissioned-room testing and explicit live opt-in. Set response-length caps, per-user throttling, concurrency limits, and a hard application-side daily API budget before enabling paid AI requests.
