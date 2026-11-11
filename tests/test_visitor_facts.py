import unittest
from bubbabot.visitor_facts import extract_safe_facts, memory_command, memory_context


class VisitorFactsTests(unittest.TestCase):
    def test_pet(self):
        self.assertEqual(extract_safe_facts("I have a dog named Coco"), ["Has a dog named Coco"])
        self.assertEqual(extract_safe_facts("my cat's name is Milo"), ["Has a cat named Milo"])

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
