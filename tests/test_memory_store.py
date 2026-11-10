"""Tests for local visitor memory without disk writes."""
import unittest
from bubbabot.memory_store import VisitorMemory


class VisitorMemoryTests(unittest.TestCase):
    def setUp(self):
        self.now = 1000000.0
        self.store = VisitorMemory(":memory:", clock=lambda: self.now)

    def tearDown(self):
        self.store.close()

    def test_remembers_a_note(self):
        self.store.remember("DavesBBS", "Sam", "Likes fishing")
        self.assertEqual(self.store.recall("davesbbs", "sam"), ["Likes fishing"])

    def test_separates_bbs_identity(self):
        self.store.remember("BBS-A", "Sam", "Likes fishing")
        self.assertEqual(self.store.recall("BBS-B", "Sam"), [])

    def test_forget(self):
        self.store.remember("BBS-A", "Sam", "Likes fishing")
        self.assertEqual(self.store.forget("BBS-A", "Sam"), 1)
        self.assertEqual(self.store.recall("BBS-A", "Sam"), [])

    def test_expiration(self):
        self.store.remember("BBS-A", "Sam", "Likes fishing")
        self.now += 91 * 86400
        self.assertEqual(self.store.recall("BBS-A", "Sam"), [])

    def test_limit(self):
        self.store.close()
        self.store = VisitorMemory(":memory:", max_notes=2, clock=lambda: self.now)
        for i in range(3):
            self.now += 1
            self.store.remember("BBS-A", "Sam", f"Note {i}")
        self.assertEqual(self.store.recall("BBS-A", "Sam"), ["Note 2", "Note 1"])

    def test_rejects_bad_notes(self):
        with self.assertRaises(ValueError):
            self.store.remember("BBS-A", "Sam", "")
        with self.assertRaises(ValueError):
            self.store.remember("BBS-A", "Sam", "x" * 241)


if __name__ == "__main__":
    unittest.main()
