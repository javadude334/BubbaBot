# BubbaBot: MRC Mode 1 SDK migration

On November 10, 2026, StackFault confirmed directly to the project owner:

- Standalone bots are permitted and recommended.
- Bots must **not interact in Lobby** or cause issues for users.
- The legacy direct TCP approach will soon be unsupported.
- Bots should use the official SDK and request a **Mode 1 connector**.
- Registration and SDK details: https://status-na-multi.relaychat.net/ecosystem/

## Current status

The developer portal was not retrievable from this environment. Its GitHub
repository and actual Python SDK event signatures are **not yet verified**.
Do not guess SDK imports, endpoints, credentials, or authentication flows.

The new `bubbabot/sdk_bridge.py` is deliberately transport-free. It accepts
`IncomingChat(user, site, room, text)` and returns `OutgoingChat(room, text)`
or `None`. It reuses the existing mention matching, cooldown, hourly limits,
and self-message filtering. Lobby is denied both in configuration and per-event.

## Integration checklist

1. Request a Mode 1 connector using the operator's developer form.
2. Obtain the SDK repository URL, documented Python installation steps,
   event schema, send method, authentication and room subscription rules.
3. Implement a separate adapter that maps **documented** SDK incoming
   messages to `IncomingChat` and outgoing replies to SDK send calls.
4. Validate SDK room subscription and enforce no Lobby interaction even if
   the SDK unexpectedly delivers Lobby messages.
5. Run local adapter tests with fake SDK events, then use an approved test
   connector and dedicated room. Never print credentials.
6. Retire the old raw TCP client from live deployment plans.

No public connection is initiated by this bridge. The historical local-only
simulator remains available for offline protocol research.
