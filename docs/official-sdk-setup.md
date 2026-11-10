# Official MRC Mode 1 SDK — BubbaBot

Reference: https://github.com/stack-fault/mrc-connector-sdk

This implementation uses the documented `MRCBot.on_message` decorator and
`MRCBot.say()` API from the official Python SDK. The SDK handles TLS,
authentication, heartbeat, and reconnection.

## Development

The real SDK has no third-party Python dependencies. Copy the official
`mrc_connector/` directory from its GitHub repository beside
`bubbabot/`, or install it according to upstream instructions. Keep
the upstream SDK source separate from our own adapter.

Run tests offline (no credentials or network connection required):

```powershell
py -3.14 -m unittest discover -s tests -v
```

## Approved connector deployment (not yet authorized)

After receiving connector approval, exact slug, host, port and token from
StackFault, provision these environment variables securely on Ubuntu:

- `CONNECTOR_HOST`: **remote MRC SDK connector server**, not the DNS name
  of the host running BubbaBot
- `CONNECTOR_PORT`: assigned TLS port (SDK documents 5010 as the default)
- `CONNECTOR_TOKEN`: issued secret; never commit it or expose in logs
- `BOT_SLUG`: exact approved connector slug
- `BOT_ROOM`: `bubba` (must match the approved dedicated room)

Then run `python3 -m bubbabot.official_sdk_runner` under a dedicated
unprivileged service user. TLS verification is always enabled in this runner.

The runner does not automatically connect to public MRC: it requires
credentials and a deliberately configured host. It refuses a room other
than `bubba`. After SDK authentication, the adapter verifies that the
server-reported `bot.room` equals `bubba` before responding. It neither
handles DMs nor sends unsolicited announcements. The approved connector
must also enforce mode 1 and the correct room server-side.

The legacy TCP simulator remains strictly loopback-only for regression
tests and is not part of the approved live connector.
