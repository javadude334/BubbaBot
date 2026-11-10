# Windows local simulation (Python 3.14)

This mode runs independently of Mystic and connects **only to 127.0.0.1**.
No public MRC network connection and no AI API charges.

## First-time setup

From PowerShell in `E:\work\javadude_dev\BubbaBot`:

```powershell
Copy-Item .\bubba.local.example.json .\bubba.local.json
```

To test the `#Bubba` room, edit the JSON values `room` to `Bubba`,
`bot_name` to `Bubba` (optional; defaults to Bubba), and `cooldown_seconds`
to `0` for a conversation test. The default interactive mock server room
is `BubbaRoom`; launch it with `--room Bubba` to match.

## Run

Terminal 1:

```powershell
py -3.14 -m bubbabot.local_test_server --room Bubba
```

Terminal 2:

```powershell
.\run-bubba-windows-local.cmd
```

Enter `Hey @Bubba` at the mock server prompt. Enter `/quit` to exit.
The bot runner permits at most three local sessions and logs to
`logs/bubbabot.log` with rotation. The interactive mock server accepts
one connection per invocation; restart the mock server to exercise another
session. Reconnection between sessions is also covered by the automated
`test_standalone_simulation` test.

## Automated tests

```powershell
py -3.14 -m unittest discover -s tests -v
```

The tests simulate separate BBS users, heartbeats, room filtering, bot
self-message suppression, and a new connection after disconnection.

## Important limitations

The simulated client handshake currently uses the legacy BBS-shaped
`ClientIdentity` for mock compatibility. This is **not** a verified or
authorized public standalone-bot handshake. Do not point this client at
the public MRC relay. The transport and settings reject non-loopback
addresses. Do not add Windows Task Scheduler or service auto-start until
a supported public bot protocol is established and TLS verification works.
