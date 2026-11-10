"""Bounded reconnect supervisor for local-only BubbaBot sessions.

No public endpoints, credential handling, or AI API. Never replays messages.
"""
import logging
import time


def run_reconnecting(make_session, *, max_sessions=3, initial_delay=1.0,
                     max_delay=30.0, sleep=time.sleep, stop=None,
                     logger=None):
    if not isinstance(max_sessions, int) or isinstance(max_sessions, bool) or max_sessions < 1:
        raise ValueError("max_sessions must be a positive integer")
    if initial_delay < 0 or max_delay < initial_delay:
        raise ValueError("invalid retry delays")
    log = logger or logging.getLogger(__name__)
    stop = stop or (lambda: False)
    attempts = 0
    total_messages = 0
    total_replies = 0
    delay = initial_delay
    while attempts < max_sessions and not stop():
        attempts += 1
        try:
            result = make_session().run()
            total_messages += result["messages"]
            total_replies += result["replies"]
            log.info("Local session %d ended messages=%d replies=%d",
                     attempts, result["messages"], result["replies"])
        except (ConnectionError, OSError, ValueError, UnicodeError) as exc:
            # No message bodies or connection credentials in event logs.
            log.warning("Local session %d failed: %s", attempts, type(exc).__name__)
        if attempts < max_sessions and not stop():
            log.info("Reconnect scheduled after %.1f seconds", delay)
            sleep(delay)
            delay = min(max_delay, delay * 2) if delay else 0
    return {"sessions": attempts, "messages": total_messages, "replies": total_replies}
