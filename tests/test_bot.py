import unittest
from bot import parse_command

class CommandParsingTests(unittest.TestCase):
    def test_simple_command(self):
        self.assertEqual(parse_command("/start", "samplebot"), ("start", ""))

    def test_command_with_arguments(self):
        self.assertEqual(parse_command("/notify hello world", "samplebot"), ("notify", "hello world"))

    def test_command_addressed_to_this_bot(self):
        self.assertEqual(parse_command("/help@samplebot", "samplebot"), ("help", ""))

    def test_command_addressed_to_another_bot_is_ignored(self):
        self.assertEqual(parse_command("/help@otherbot", "samplebot"), (None, ""))

    def test_non_command_is_ignored(self):
        self.assertEqual(parse_command("hello", "samplebot"), (None, ""))

if __name__ == "__main__":
    unittest.main()
