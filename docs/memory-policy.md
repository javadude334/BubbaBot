# BubbaBot visitor memory policy (design decision)

Status: **Approved design; implementation incomplete.** No automatic memory extraction or AI conversation integration is deployed yet.

## Default behavior

- Automatically retain **useful, non-sensitive, explicitly stated** visitor details (e.g. hobbies, favorite music, pets, upcoming activities).
- At the first interaction, give a concise notice that memory is enabled and explain how to review, forget, and opt out.
- Keep memory scoped to the combination of originating BBS and MRC handle. This is a namespace, **not proof of identity**; account impersonation/reassignment risks must be evaluated before exposing stored details.
- Do not store passwords, tokens, addresses, phone numbers, medical/financial details, or other sensitive information automatically. Do not infer personal facts.
- Do not repeat one visitor's stored details to another visitor. In public rooms, avoid volunteering remembered personal details without clear contextual reason.
- Proposed commands: `.memory` (review), `.forget` (delete), `.privacy` (explain), `.memory off` (opt out and delete), `.memory on` (opt in).
- Retain a maximum of 12 short notes per visitor; default expiration 90 days. Revisit after user testing.
- Provide a privacy notice before any AI API transmission. Keep the bot strictly within approved `#bubba`; never `#lobby`.
- Make storage errors fail closed (no silent unprotected fallback). Keep memory data outside the read-only application directory, in a service-writable directory with restrictive permissions.
- Never commit credentials or visitor memories to Git.

## Implementation notes

`bubbabot/memory_store.py` currently provides an offline SQLite prototype for short notes, expiry, per-(BBS, handle) namespaces and deletion. **It is not yet wired into the bot or the AI provider.** Automatic extraction, privacy notice, commands, opt-out enforcement, sensitive-content filtering, authentication/identity limitations, and persistence tests are still pending.

The user is checking whether PostgreSQL is installed on the Ubuntu host. Select the production backend after confirming what is available; do not assume PostgreSQL is present.

## Testing before release

Test consent notice, opt-out, delete, TTL expiry, sensitive-data exclusion, cross-user isolation, prompt injection resistance, rate limits, memory recall correctness, and disk/DB failure behavior. Keep live MRC service disabled pending StackFault approval.
