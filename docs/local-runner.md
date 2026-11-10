# Local-only runner

This is a developer tool, **not a live MRC connector**. It accepts only numeric loopback addresses. Do not change that restriction to access the shared MRC network; await approved connector specifications.

## Windows

1. Copy `bubba.local.example.json` to `bubba.local.json` and adjust the room and local test port.
2. Start a local simulated server on that port (the unit tests include a mock server).
3. Run `run-bubba-local.cmd` from the repository folder.
4. Stop with Ctrl+C. Rotating event logs are stored under `logs/` (no chat content is logged).

## Linux / Ubuntu

Use Python 3.10+:

```sh
cp bubba.local.example.json bubba.local.json
python3 -m unittest discover -s tests -v
python3 -m bubbabot.local_runner --config bubba.local.json
```

The client connects once and exits on disconnect; automatic reconnect for a live bot remains unimplemented. The existing connection manager has separate loopback-only reconnect tests. No OpenAI API requests are made.
