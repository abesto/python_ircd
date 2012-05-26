# coding=utf-8

import unittest

import abnf
import config


class AbnfTest(unittest.TestCase):
    def setUp(self):
        config.traling_spaces = False
        config.soft_eol = False
        reload(abnf)

    def _test(self, parser, cases):
        for input, expected in cases.iteritems():
            actual = abnf.parse(input, parser)
            #print input, expected, actual
            self.assertEqual(expected, actual)

    def test_nickname(self):
        self._test(abnf.nickname, {
            '333': False,
            'abcd': 'abcd',
            '[]\`_^{|}': '[]\`_^{|}'
        })

    def test_command(self):
        self._test(abnf.command, {
            '1': False,
            '11': False,
            '100': '100',
            '2fo': False,
            'foo2': False,
            'fooBAR': 'fooBAR'
        })

    def test_params(self):
        self._test(abnf.params, {
            '': '',
            ' ': '',
            ' a': ['a'],
            ' a  b': False,
            ' a b': ['a', 'b'],
            ' a b :asdf qwer': ['a', 'b', 'asdf qwer'],
            ' 1 2 3 4 5 6 7 8 9 10 11 12 13 14 asdf qwer': [str(i) for i in range(1,15)] + ['asdf qwer'],
            ' 1 2 3 4 5 6 7 8 9 10 11 12 13 14 :asdf qwer': [str(i) for i in range(1,15)] + ['asdf qwer']
        })

    def test_shortname(self):
        self._test(abnf.shortname, {
            '': False,
            'a': 'a',
            'foobar': 'foobar',
            'a-foob-baz': 'a-foob-baz'
        })

    def test_hostname(self):
        self._test(abnf.hostname, {
            '': False,
            'a': 'a',
            'a-b': 'a-b',
            'a-b.': False,
            'a-b.c': 'a-b.c',
            'a.b-c': 'a.b-c',
            'a-b.c-': 'a-b.c-',  # This looks wrong, but the grammar in RFC2812 allows it
            'a-b.c-d.ef': 'a-b.c-d.ef'
        })

    def test_ip4addr(self):
        self._test(abnf.ip4addr, {
            '': False,
            '1.': False,
            '1.2': False,
            '1.2.': False,
            '1.2.3': False,
            '1.2.3.': False,
            '1.2.3.4': '1.2.3.4',
            '1.2.3.4.': False,
            '.1.2.3.4': False,
            '127.0.0.1': '127.0.0.1',
            '0.0.0.0': '0.0.0.0',
            '999.999.999.999': '999.999.999.999'
        })

    def test_user(self):
        self._test(abnf.user, {
            'a b': False,
            'a\rb': False,
            'a\nb': False,
            'a@b': False,
            'asdf': 'asdf',
            '!#^QWER': '!#^QWER'
        })

    def test_message(self):
        self._test(abnf.message, {
            'JOIN #a\r\n': ['', 'JOIN', '#a'],
            ':prefix COMMAND param1 :param is long\r\n': ['prefix', 'COMMAND', 'param1', 'param is long']
        })


    def test_trailing_spaces(self):
        self.assertFalse(abnf.parse('JOIN #a \r\n', abnf.message))
        config.traling_spaces = True
        reload(abnf)
        self.assertListEqual(['', 'JOIN', '#a'], abnf.parse('JOIN #a   \r\n', abnf.message))

    def test_soft_eol(self):
        self.assertFalse(abnf.parse('JOIN #a\r', abnf.message))
        self.assertFalse(abnf.parse('JOIN #a\n', abnf.message))
        config.soft_eol = True
        reload(abnf)
        self._test(abnf.message, {
            'JOIN #a\r': ['', 'JOIN', '#a'],
            'JOIN #a\n': ['', 'JOIN', '#a']
        })

    def test_regr01(self):
        """
        Regression in 119da40fc8a2ddfb885d6687b7dddd90144d2995
        Problem: Fails to parse \r\n terminated messages when soft_eol is on
        """
        config.soft_eol = True
        reload(abnf)
        self.assertEqual(['', 'JOIN', '#a'], abnf.parse('JOIN #a\r\n', abnf.message))

    def test_trailing_spaces_and_soft_eol(self):
        config.soft_eol = True
        config.traling_spaces = True
        reload(abnf)
        self.assertListEqual(['', 'JOIN', '#a'], abnf.parse('JOIN #a   \r', abnf.message))


    def test_channel(self):
        self._test(abnf.channel, {
            '#foo': ['#', 'foo'],
            '#foo:bar': ['#', 'foo', 'bar'],
            '!12345foo': ['!', '12345', 'foo'],
            '!12345foo:barbaz': ['!', '12345', 'foo', 'barbaz']
        })

