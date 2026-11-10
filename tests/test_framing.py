import unittest

from bubbabot.framing import MRCLineFramer


class MRCLineFramerTests(unittest.TestCase):
    def test_split_packet(self):
        f = MRCLineFramer()
        self.assertEqual(f.feed(b"A~B~"), [])
        self.assertEqual(f.feed(b"C~D~E~F~hello~\n"), ["A~B~C~D~E~F~hello~\n"])
        f.finish()

    def test_multiple_packets_and_partial_tail(self):
        f = MRCLineFramer()
        self.assertEqual(f.feed(b"one\ntwo\npar"), ["one\n", "two\n"])
        self.assertEqual(f.feed(b"tial\n"), ["partial\n"])
        f.finish()

    def test_utf8_split_across_reads(self):
        f = MRCLineFramer()
        encoded = "hello café\n".encode("utf-8")
        self.assertEqual(f.feed(encoded[:-2]), [])
        self.assertEqual(f.feed(encoded[-2:]), ["hello café\n"])

    def test_large_response_many_lines(self):
        f = MRCLineFramer()
        records = [f"BBS {n}~\n" for n in range(250)]
        raw = "".join(records).encode()
        result = []
        for offset in range(0, len(raw), 13):
            result.extend(f.feed(raw[offset:offset + 13]))
        self.assertEqual(result, records)
        f.finish()

    def test_rejects_oversized_partial_packet(self):
        f = MRCLineFramer(max_line_bytes=8)
        with self.assertRaises(ValueError):
            f.feed(b"123456789")

    def test_rejects_oversized_complete_packet(self):
        f = MRCLineFramer(max_line_bytes=8)
        with self.assertRaises(ValueError):
            f.feed(b"123456789\n")

    def test_rejects_invalid_utf8(self):
        f = MRCLineFramer()
        with self.assertRaises(ValueError):
            f.feed(b"\xff\n")

    def test_rejects_unterminated_final_packet(self):
        f = MRCLineFramer()
        f.feed(b"partial")
        with self.assertRaises(ValueError):
            f.finish()


if __name__ == "__main__":
    unittest.main()
