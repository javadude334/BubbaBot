# Independent MRC connector — offline research

Source examined: StackFault / Phenom Productions MRC multiplexer v1.3.7
(`mrc_client.py` and `mrc_config.py` supplied by the operator of Dave's BBS).

## Confirmed from client source

- SSL port is configured as 5001; plain port as 5000. These are settings, not a guarantee of current server availability.
- Initial identification is sent as `bbsname~MYSTIC/<os>/<arch>/1.3.7` without a newline.
- Following connection, the multiplexer sends BBS information, `IMALIVE`, and `CAPABILITIES` control packets.
- Chat and control records have seven tilde-separated fields, ending in `~` and typically a newline.
- The client responds to server `PING` with an `IMALIVE` control packet.
- Mystic and the multiplexer communicate through files under the Mystic installation; the multiplexer forwards server messages to active chat node directories.
- The original client splits each individual `recv(16384)` by newline without preserving incomplete trailing fragments. TCP can split or coalesce records, so a standalone implementation must buffer across reads.
- The configured server certificate was reported expired in November 2026 when tested with modern Python TLS verification. Do not disable certificate verification to work around it.

## Unknown — not established by client source

- Whether the current public relay permits independent automated clients or bots.
- Whether a standalone bot can authenticate without claiming a BBS identity.
- How the live server authorizes or joins bot rooms and how bot attribution is represented.
- Whether the currently hosted server accepts this exact legacy handshake.
- Whether the network has additional anti-spam, registration, or traffic limits.

## Implementation plan

1. Keep the existing local mock MRC tests and routing behavior.
2. Test incremental line framing, including multiple records per TCP read, fragmented UTF-8, oversized records, and bursts of more than 100 lines.
3. Introduce an adapter boundary for future independent-client authentication; never reuse Dave's BBS credentials or identity.
4. Add a local-only server fixture that verifies handshake/control traffic and reconnect behavior.
5. Require documented operator permission, validated TLS, and explicit configuration before any public connection.

No production connection, network scan, or bot identity registration is part of this phase.
