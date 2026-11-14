"""Offline tests for fictional world persistence (no API calls)."""
import tempfile
import unittest
from pathlib import Path

from bubbabot.world_memory import WorldMemory


class WorldMemoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "possum-creek.sqlite"
        self.world = WorldMemory(self.path)
        self.world.initialize()

    def test_event_persists_across_restart_and_deduplicates(self):
        kwargs = dict(kind="shooting", summary="Bertha May shot Charlie.",
                      characters=("Bertha May", "Charlie"), severity="critical")
        event_id = self.world.record_event(**kwargs)
        again = WorldMemory(self.path)
        again.initialize()
        self.assertEqual(event_id, again.record_event(**kwargs))
        event = again.event(event_id)
        self.assertEqual(event["status"], "developing")
        self.assertEqual(event["severity"], "critical")
        self.assertNotIn("hospital", event["summary"].lower())

    def test_update_delivered_only_to_visitor(self):
        event_id = self.world.record_event(kind="shooting",
                                           summary="Bertha May shot Charlie.")
        update_id = self.world.add_update(event_id,
            "Charlie is home from the hospital; Bertha May is still in jail.")
        self.assertEqual(self.world.unseen_updates("Dave's BBS", "javadude")[0]["id"],
                         update_id)
        self.world.mark_delivered("Dave's BBS", "javadude", update_id)
        self.assertEqual(self.world.unseen_updates("dave's bbs", "JAVADUDE"), [])
        self.assertEqual(len(self.world.unseen_updates("Dave's BBS", "bamageek")), 1)

    def test_reject_nonfiction_provenance(self):
        with self.assertRaises(ValueError):
            self.world.record_event(kind="crime", summary="Real-world accusation",
                                    provenance="real_news")


if __name__ == "__main__":
    unittest.main()
