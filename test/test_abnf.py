# coding=utf-8

import unittest

import abnf
import config


class AbnfTest(unittest.TestCase):
    def setUp(self):
        config.traling_spaces = False
        config.soft_eol = False
        reload(abnf)

    def _cases(self, parser, cases):
        for input, expected in cases.iteritems():
            actual = abnf.parse(input, parser)
            #print input, expected, actual
            self.assertEqual(expected, actual)

    def test_nickname(self):
        self.assertFalse(abnf.parse('333', abnf.nickname))
        self.assertEqual('abcd', abnf.parse('abcd', abnf.nickname))
        self.assertEqual('[]\`_^{|}', abnf.parse('[]\`_^{|}', abnf.nickname))

    def test_command(self):
        self.assertFalse(abnf.parse('1', abnf.command))
        self.assertFalse(abnf.parse('11', abnf.command))
        self.assertEqual('100', abnf.parse('100', abnf.command))

        self.assertFalse(abnf.parse('2fo', abnf.command))
        self.assertFalse(abnf.parse('foo2', abnf.command))

        self.assertEqual('fooBAR', abnf.parse('fooBAR', abnf.command))

    def test_params(self):
        cases = {
            '': '',
            ' ': '',
            ' a': ['a'],
            ' a  b': False,
            ' a b': ['a', 'b'],
            ' a b :asdf qwer': ['a', 'b', 'asdf qwer'],
            ' 1 2 3 4 5 6 7 8 9 10 11 12 13 14 asdf qwer': [str(i) for i in range(1,15)] + ['asdf qwer'],
            ' 1 2 3 4 5 6 7 8 9 10 11 12 13 14 :asdf qwer': [str(i) for i in range(1,15)] + ['asdf qwer']
        }
        for input, output in cases.iteritems():
            self.assertEqual(output, abnf.parse(input, abnf.params))

    def test_shortname(self):
        cases = {
            '': False,
            'a': 'a',
            'a-b': 'a-b'
        }
        for input, output in cases.iteritems():
            self.assertEqual(output, abnf.parse(input, abnf.shortname))

    def test_hostname(self):
        self._cases(abnf.hostname, {
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
        cases = {
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
        }
        for input, output in cases.iteritems():
            self.assertEqual(output, abnf.parse(input, abnf.ip4addr))

    def test_user(self):
        self._cases(abnf.user, {
            'a b': False,
            'a\rb': False,
            'a\nb': False,
            'a@b': False,
            'asdf': 'asdf',
            '!#^QWER': '!#^QWER'
        })

    def test_message(self):
        self._cases(abnf.message, {
            'JOIN #a\r\n': ['', 'JOIN', '#a'],
            ':prefix COMMAND param1 :param is long\r\n': [':prefix', 'COMMAND', 'param1', 'param is long']
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
        self._cases(abnf.message, {
            'JOIN #a\r': ['', 'JOIN', '#a'],
            'JOIN #a\n': ['', 'JOIN', '#a']
        })

    def test_regr01(self):
        """
        Regression in 119da40fc8a2ddfb885d6687b7dddd90144d2995
        Problem: Fails to parse \r\n terminated messages when soft_eol is on
        Solution: try crlf first
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
        self._cases(abnf.channel, {
            '#foo': ['#', 'foo'],
            '#foo:bar': ['#', 'foo', 'bar'],
            '!12345foo': ['!', '12345', 'foo'],
            '!12345foo:barbaz': ['!', '12345', 'foo', 'barbaz']
        })

