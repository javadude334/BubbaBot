# Getting BubbaBot onto shared Multi Relay Chat (MRC)

## Status

BubbaBot currently passes 34 offline tests including simulated TCP handshake, heartbeat, room message, and reply. **It does not connect to the shared MRC network.** The source-derived handshake is for a historical Mystic client, not an approved standalone bot.

## Operator questions

Contact the operator of the MRC network used by Dave's BBS (the MRC wiki names StackFault as a developer contact). Ask:

1. Are standalone automated bot clients permitted on this network, and what approval/registration is required?
2. Is there an **MRC-specific** SDK or connector protocol for bots? Request its official repository and documentation. Do not confuse it with unrelated products called Relay.
3. What client identification, authentication, TLS, keepalive, and capability announcements are required?
4. How does a bot join a designated room, and what restrictions apply to posting, mentions, rate limits, and reconnects?
5. Is there a sanctioned testing room or private test server?

## Proposed first live test

- Name: Bubba (clearly identified as an automated chatbot)
- Function: Reply with a fixed greeting only when directly mentioned with `@Bubba`
- Room: Operator-approved room only
- Limits: One reply per sender per 30 seconds, 20 replies/hour globally; no unsolicited messages
- Credentials: Environment variables only, never GitHub or logs
- Network: Explicit live-mode opt-in only after operator confirmation
- Stop: Manual termination; no auto-start until the first test succeeds
- AI API: Disabled; no cost

## Reference

MRC project: https://sourceforge.net/projects/mystic-relay-chat/
MRC wiki: https://bbswiki.bottomlessabyss.net/index.php?title=MRC_Chat_platform

The publicly surfaced MRC wiki states that developers creating new clients should reach out to StackFault. It does not, on its own, verify an SDK announcement or grant bot access.
