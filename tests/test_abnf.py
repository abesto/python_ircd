# coding=utf-8

import unittest

from config import config
from include import abnf


class AbnfTest(unittest.TestCase):
    def setUp(self):
        config.set("parser", "trailing_spaces", "false")
        config.set("parser", "soft_eol", "false")
        self.parser = abnf.default_parser()

    def _test(self, parser, cases):
        for input, expected in cases.items():
            actual = self.parser.parse(input, parser)
            # print input, expected, actual
            self.assertEqual(expected, actual)

    def test_nickname(self):
        self._test(
            self.parser.nickname,
            {"333": None, "abcd": "abcd", "[]\`_^{|}": "[]\`_^{|}"},
        )

    def test_command(self):
        self._test(
            self.parser.command,
            {
                "1": None,
                "11": None,
                "100": "100",
                "2fo": None,
                "foo2": None,
                "fooBAR": "fooBAR",
            },
        )

    def test_params(self):
        self._test(
            self.parser.params,
            {
                "": "",
                " ": "",
                " a": ["a"],
                " a  b": None,
                " a b": ["a", "b"],
                " a b :asdf qwer": ["a", "b", "asdf qwer"],
                " 1 2 3 4 5 6 7 8 9 10 11 12 13 14 asdf qwer": [
                    str(i) for i in range(1, 15)
                ]
                + ["asdf qwer"],
                " 1 2 3 4 5 6 7 8 9 10 11 12 13 14 :asdf qwer": [
                    str(i) for i in range(1, 15)
                ]
                + ["asdf qwer"],
            },
        )

    def test_shortname(self):
        self._test(
            self.parser.shortname,
            {"": None, "a": "a", "foobar": "foobar", "a-foob-baz": "a-foob-baz"},
        )

    def test_hostname(self):
        self._test(
            self.parser.hostname,
            {
                "": None,
                "a": "a",
                "a-b": "a-b",
                "a-b.": None,
                "a-b.c": "a-b.c",
                "a.b-c": "a.b-c",
                # This looks wrong, but the grammar in RFC2812 allows it
                "a-b.c-": "a-b.c-",
                "a-b.c-d.ef": "a-b.c-d.ef",
            },
        )

    def test_ip4addr(self):
        self._test(
            self.parser.ip4addr,
            {
                "": None,
                "1.": None,
                "1.2": None,
                "1.2.": None,
                "1.2.3": None,
                "1.2.3.": None,
                "1.2.3.4": "1.2.3.4",
                "1.2.3.4.": None,
                ".1.2.3.4": None,
                "127.0.0.1": "127.0.0.1",
                "0.0.0.0": "0.0.0.0",
                "999.999.999.999": "999.999.999.999",
            },
        )

    def test_user(self):
        self._test(
            self.parser.user,
            {
                "a b": None,
                "a\rb": None,
                "a\nb": None,
                "a@b": None,
                "asdf": "asdf",
                "!#^QWER": "!#^QWER",
            },
        )

    def test_message(self):
        self._test(
            self.parser.message,
            {
                "JOIN #a\r\n": ["", "JOIN", "#a"],
                ":prefix COMMAND param1 :param is long\r\n": [
                    "prefix",
                    "COMMAND",
                    "param1",
                    "param is long",
                ],
            },
        )

    def test_trailing_spaces(self):
        self.assertIsNone(self.parser.parse("JOIN #a \r\n", self.parser.message))
        config.set("parser", "trailing_spaces", "true")
        self.assertListEqual(
            ["", "JOIN", "#a"], self.parser.parse("JOIN #a   \r\n", self.parser.message)
        )

    def test_soft_eol(self):
        self.assertIsNone(self.parser.parse("JOIN #a\r", self.parser.message))
        self.assertIsNone(self.parser.parse("JOIN #a\n", self.parser.message))
        config.set("parser", "soft_eol", "true")
        self._test(
            self.parser.message,
            {"JOIN #a\r": ["", "JOIN", "#a"], "JOIN #a\n": ["", "JOIN", "#a"]},
        )

    def test_regr01(self):
        """
        Regression in 119da40fc8a2ddfb885d6687b7dddd90144d2995
        Problem: Fails to parse \r\n terminated messages when soft_eol is on
        """
        config.set("parser", "soft_eol", "true")
        self.assertEqual(
            ["", "JOIN", "#a"], self.parser.parse("JOIN #a\r\n", self.parser.message)
        )

    def test_trailing_spaces_and_soft_eol(self):
        config.set("parser", "soft_eol", "true")
        config.set("parser", "trailing_spaces", "true")
        self.assertListEqual(
            ["", "JOIN", "#a"], self.parser.parse("JOIN #a   \r", self.parser.message)
        )

    def test_channel(self):
        self._test(
            self.parser.channel,
            {
                "#foo": ["#", "foo"],
                "#foo:bar": ["#", "foo", "bar"],
                "!12345foo": ["!", "12345", "foo"],
                "!12345foo:barbaz": ["!", "12345", "foo", "barbaz"],
            },
        )

    def test_wildcards(self):
        self._test(
            self.parser.wildcard("a?b"),
            {"abb": "abb", "a3b": "a3b", "ab": None, "xab": None, "abx": None},
        )
        self._test(
            self.parser.wildcard("a*b"),
            {"ab": "ab", "a foobar b": "a foobar b", "qab": None, "abq": None},
        )
