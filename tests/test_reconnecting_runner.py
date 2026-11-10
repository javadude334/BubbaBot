import unittest

from bubbabot.reconnecting_runner import run_reconnecting


class ReconnectSupervisorTests(unittest.TestCase):
    def test_disconnect_reconnect_without_replay(self):
        created = []
        delays = []

        class FakeSession:
            def __init__(self, number):
                self.number = number

            def run(self):
                if self.number == 1:
                    raise ConnectionError("simulated disconnect")
                return {"messages": 2, "replies": 1}

        def make_session():
            created.append(FakeSession(len(created) + 1))
            return created[-1]

        result = run_reconnecting(make_session, max_sessions=3,
                                  initial_delay=1, max_delay=2, sleep=delays.append)
        self.assertEqual(result, {"sessions": 3, "messages": 4, "replies": 2})
        self.assertEqual(delays, [1, 2])
        self.assertEqual(len(created), 3)

    def test_stop_prevents_connecting(self):
        result = run_reconnecting(lambda: self.fail("should not connect"),
                                  stop=lambda: True)
        self.assertEqual(result["sessions"], 0)

    def test_invalid_settings(self):
        with self.assertRaises(ValueError):
            run_reconnecting(lambda: None, max_sessions=0)
        with self.assertRaises(ValueError):
            run_reconnecting(lambda: None, initial_delay=-1)

    def test_application_errors_not_swallowed(self):
        class Broken:
            def run(self):
                raise RuntimeError("programming bug")
        with self.assertRaises(RuntimeError):
            run_reconnecting(lambda: Broken(), max_sessions=1)


if __name__ == "__main__":
    unittest.main()
