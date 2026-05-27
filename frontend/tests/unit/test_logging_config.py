"""Tests for centralized logging level helpers."""

import logging
import unittest

from frontend.utils import parse_log_level


class TestParseLogLevel(unittest.TestCase):
    def test_known_levels(self):
        self.assertEqual(parse_log_level("DEBUG"), logging.DEBUG)
        self.assertEqual(parse_log_level("INFO"), logging.INFO)
        self.assertEqual(parse_log_level("WARNING"), logging.WARNING)

    def test_empty_uses_default(self):
        self.assertEqual(parse_log_level(None), logging.INFO)
        self.assertEqual(parse_log_level(""), logging.INFO)

    def test_unknown_name_falls_back_to_default(self):
        self.assertEqual(parse_log_level("not_a_real_level"), logging.INFO)


if __name__ == "__main__":
    unittest.main()
