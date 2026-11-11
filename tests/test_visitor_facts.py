import unittest
from unittest.mock import Mock
from bubbabot.lan_mrc_adapter import memory_command_reply
from bubbabot.visitor_facts import extract_safe_facts, memory_command, memory_context, normalize_mrc_message


class VisitorFactsTests(unittest.TestCase):
    def test_pet(self):
        self.assertEqual(extract_safe_facts("I have a dog named Coco"), ["Has a dog named Coco"])
        self.assertEqual(extract_safe_facts("my cat's name is Milo"), ["Has a cat named Milo"])

    def test_casual_pet_mention(self):
        self.assertEqual(extract_safe_facts("Been looking for my dog Coco"), ["Has a dog named Coco"])

    def test_formatted_commands(self):
        self.assertEqual(memory_command("|03@bubba what do you remember about me?"), "recall")
        self.assertEqual(memory_command("@bubba, what do you remember about me?!"), "recall")
        self.assertEqual(memory_command("@bubba forget me!"), "forget")

    def test_addressed_pet_is_safe(self):
        self.assertEqual(extract_safe_facts("@bubba I have a dog named Coco"), ["Has a dog named Coco"])
        self.assertEqual(extract_safe_facts("@bubba I have a cat named Kaykay"), ["Has a cat named Kaykay"])
        self.assertEqual(extract_safe_facts("@bubba my email is bob@example.com and I have a dog named Coco"), [])

    def test_memory_round_trip_without_ai(self):
        # Exercises the same parser, storage calls and command handler as MRC.
        notes = {}
        memory = Mock()
        memory.remember_screened.side_effect = lambda site, user, note: notes.setdefault((site, user), []).append(note)
        memory.recall.side_effect = lambda site, user: notes.get((site, user), [])
        memory.forget.side_effect = lambda site, user: notes.pop((site, user), None)
        for message in ("@bubba I have a dog named Coco", "I have a cat named Kaykay"):
            for fact in extract_safe_facts(message):
                memory.remember_screened("davesbbs.com", "bamageek", fact)
        response = memory_command_reply(memory_command("What do you remember about me?"), memory, "davesbbs.com", "bamageek")
        self.assertIn("Coco", response)
        self.assertIn("Kaykay", response)
        self.assertEqual(memory_command_reply("forget", memory, "davesbbs.com", "bamageek"),
                         "Done. I cleared what I remembered about you.")
        self.assertIn("don't have any", memory_command_reply("recall", memory, "davesbbs.com", "bamageek"))

    def test_memory_command_failure_does_not_claim_deletion(self):
        memory = Mock()
        memory.forget.side_effect = RuntimeError("offline")
        self.assertNotIn("Done.", memory_command_reply("forget", memory, "bbs", "handle"))

    def test_mystic_colored_sender_prefix(self):
        message = "|02<|10BamaGeek|02>|16|07 @bubba I have a dog named Coco"
        cleaned = normalize_mrc_message(message, "BamaGeek")
        self.assertEqual(cleaned, "@bubba I have a dog named Coco")
        self.assertEqual(extract_safe_facts(cleaned), ["Has a dog named Coco"])
        question = normalize_mrc_message(
            "|02<|10BamaGeek|02>|16|07 @bubba what do you remember about me?", "BamaGeek")
        self.assertEqual(memory_command(question), "recall")

    def test_does_not_strip_other_users_prefix(self):
        self.assertEqual(normalize_mrc_message("<Alice> hello", "Bob"), "<Alice> hello")

    def test_interests(self):
        self.assertEqual(extract_safe_facts("I love fishing"), ["Enjoys fishing"])

    def test_sensitive_information_not_stored(self):
        self.assertEqual(extract_safe_facts("My email is bob@example.com. I have a dog named Coco"), [])
        self.assertEqual(extract_safe_facts("I have a dog named Coco and my phone is 555-123-4567"), [])
        self.assertEqual(extract_safe_facts("I have a dog named Coco and my password is secret"), [])

    def test_commands(self):
        self.assertEqual(memory_command("@bubba what do you remember about me?"), "recall")
        self.assertEqual(memory_command("Bubba forget me"), "forget")
        self.assertIsNone(memory_command("I forgot my dog food"))

    def test_context(self):
        self.assertIn("Has a dog named Coco", memory_context(["Has a dog named Coco"]))
        self.assertEqual(memory_context([]), "")


if __name__ == "__main__":
    unittest.main()
