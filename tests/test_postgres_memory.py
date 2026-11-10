"""Offline tests for PostgreSQL memory identity and validation."""
import unittest
from bubbabot.postgres_memory import PostgresVisitorMemory


class PostgresMemoryTests(unittest.TestCase):
    def setUp(self):
        self.store = PostgresVisitorMemory(secret=b"x" * 32)

    def test_key_stable(self):
        self.assertEqual(self.store._key("Dave", "SAM"), self.store._key("dave", "sam"))

    def test_bbs_separation(self):
        self.assertNotEqual(self.store._key("Dave", "sam"), self.store._key("Other", "sam"))

    def test_does_not_embed_identity(self):
        self.assertNotIn("sam", self.store._key("Dave", "sam"))

    def test_short_secret_rejected(self):
        with self.assertRaises(ValueError):
            PostgresVisitorMemory(secret=b"short")

    def test_empty_identity_rejected(self):
        with self.assertRaises(ValueError):
            self.store._key("", "sam")


if __name__ == "__main__":
    unittest.main()
