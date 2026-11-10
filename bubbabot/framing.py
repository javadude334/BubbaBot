"""Bounded, incremental MRC line framing for stream transports.

TCP reads are arbitrary chunks, not message boundaries. This decoder never
returns an incomplete record and rejects unbounded or malformed input.
"""
class MRCLineFramer:
    def __init__(self, max_line_bytes=16384):
        if not isinstance(max_line_bytes, int) or isinstance(max_line_bytes, bool) or max_line_bytes < 1:
            raise ValueError("max_line_bytes must be positive")
        self.max_line_bytes = max_line_bytes
        self._pending = bytearray()

    def feed(self, chunk: bytes) -> list[str]:
        if not isinstance(chunk, bytes):
            raise TypeError("chunk must be bytes")
        self._pending.extend(chunk)
        result = []
        while True:
            end = self._pending.find(b"\n")
            if end < 0:
                break
            if end + 1 > self.max_line_bytes:
                self._pending.clear()
                raise ValueError("MRC packet exceeds maximum length")
            line = bytes(self._pending[:end + 1])
            del self._pending[:end + 1]
            try:
                result.append(line.decode("utf-8"))
            except UnicodeDecodeError as exc:
                self._pending.clear()
                raise ValueError("invalid UTF-8 MRC packet") from exc
        if len(self._pending) > self.max_line_bytes:
            self._pending.clear()
            raise ValueError("MRC packet exceeds maximum length")
        return result

    def finish(self):
        if self._pending:
            raise ValueError("unterminated MRC packet")
