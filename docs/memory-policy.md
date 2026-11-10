# BubbaBot visitor memory policy (design decision)

Status: **Approved design; implementation incomplete.** No automatic memory extraction or AI conversation integration is deployed yet.

## Default behavior

- Automatically retain **useful, non-sensitive, explicitly stated** visitor details (e.g. hobbies, favorite music, pets, upcoming activities).
- At the first interaction, give a concise notice that memory is enabled and explain how to review, forget, and opt out.
- Scope memory by originating BBS and MRC handle without storing raw identifiers in note text. Prefer a keyed pseudonymous lookup (e.g., HMAC) rather than raw handles in the production database; this is still pseudonymous personal data, not true anonymity. MRC handle alone is **not proof of identity**; account impersonation/reassignment risks must be evaluated before exposing stored details.
- **Never retain PII in long-term conversational memory:** exclude real names, postal addresses, phone numbers, email addresses, birthdays, workplaces, precise locations, government/account identifiers, credentials, and sensitive medical/financial details. Do not infer personal facts. Apply exclusion before any database write; treat uncertain cases as non-storable.
- Do not repeat one visitor's stored details to another visitor. In public rooms, avoid volunteering remembered personal details without clear contextual reason.
- Proposed commands: `.memory` (review), `.forget` (delete), `.privacy` (explain), `.memory off` (opt out and delete), `.memory on` (opt in).
- Retain a maximum of 12 short notes per visitor; default expiration 90 days. Revisit after user testing.
- Provide a privacy notice before any AI API transmission. Keep the bot strictly within approved `#bubba`; never `#lobby`.
- Make storage errors fail closed (no silent unprotected fallback). Keep memory data outside the read-only application directory, in a service-writable directory with restrictive permissions.
- Never commit credentials or visitor memories to Git.

## Implementation notes

`bubbabot/memory_store.py` currently provides an offline SQLite prototype for short notes, expiry, per-(BBS, handle) namespaces and deletion. **It is not yet wired into the bot or the AI provider.** Automatic extraction, privacy notice, commands, opt-out enforcement, sensitive-content filtering, authentication/identity limitations, and persistence tests are still pending.

PostgreSQL 16.15 is installed and listening on 127.0.0.1:5432 on the Ubuntu host. Use a dedicated least-privilege database and role after verifying the PostgreSQL cluster; do not expose PostgreSQL publicly. The SQLite prototype is not yet production storage.

## Testing before release

Test consent notice, opt-out, delete, TTL expiry, sensitive-data exclusion, cross-user isolation, prompt injection resistance, rate limits, memory recall correctness, and disk/DB failure behavior. Keep live MRC service disabled pending StackFault approval.
