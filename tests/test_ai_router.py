"""Offline tests; no credentials, sockets or API charges."""
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from bubbabot.ai.base import AIError, AIResponse
from bubbabot.ai.budget import MonthlyBudget
from bubbabot.ai.router import AIRouter


class Fake:
    def __init__(self, name, error=None):
        self.name, self.error, self.calls = name, error, 0

    def generate(self, messages):
        self.calls += 1
        if self.error:
            raise AIError(self.error)
        return AIResponse("Howdy!", self.name)


class RouterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.budget = MonthlyBudget(str(Path(self.temp.name) / "budget.json"), "0.02")

    def test_cloud_first_then_budget_fallback(self):
        cloud, local = Fake("openai"), Fake("ollama")
        router = AIRouter(cloud, local, self.budget)
        self.assertEqual(router.generate([]).provider, "openai")
        self.assertEqual(router.generate([]).provider, "openai")
        self.assertEqual(router.generate([]).provider, "ollama")
        self.assertEqual((cloud.calls, local.calls), (2, 1))

    def test_quota_disables_cloud(self):
        cloud, local = Fake("openai", "quota"), Fake("ollama")
        router = AIRouter(cloud, local, self.budget)
        self.assertEqual(router.generate([]).provider, "ollama")
        self.assertEqual(router.generate([]).provider, "ollama")
        self.assertEqual(cloud.calls, 1)

    def test_rate_limit_falls_back(self):
        cloud, local = Fake("openai", "rate_limit"), Fake("ollama")
        self.assertEqual(AIRouter(cloud, local, self.budget).generate([]).provider, "ollama")

    def test_persists_spend(self):
        self.budget.charge(Decimal("0.01"))
        again = MonthlyBudget(str(Path(self.temp.name) / "budget.json"), "0.02")
        self.assertEqual(again.remaining(), Decimal("0.01"))

    def test_rejects_negative_charge(self):
        with self.assertRaises(ValueError):
            self.budget.charge(Decimal("-0.01"))


if __name__ == "__main__":
    unittest.main()
