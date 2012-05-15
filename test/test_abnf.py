import unittest
from abnf import *

class AbnfTest(unittest.TestCase):
    def test_nickname(self):
        self.assertFalse(parse('333', nickname).parsed)
        self.assertEqual('abcd', parse('abcd', nickname).parsed)
        self.assertEqual('[]\`_^{|}', parse('[]\`_^{|}', nickname).parsed)

    def test_command(self):
        self.assertFalse(parse('1', command).parsed)
        self.assertFalse(parse('11', command).parsed)
        self.assertEqual('100', parse('100', command).parsed)

        self.assertFalse(parse('2fo', command).parsed)
        self.assertFalse(parse('foo2', command).parsed)

        self.assertEqual('fooBAR', parse('fooBAR', command).parsed)

    def test_params(self):
        cases = {
            '': False,
            ' ': False,
            ' a': ['a'],
            ' a  b': False,
            ' a b': ['a', 'b'],
            ' a b :asdf qwer': ['a', 'b', 'asdf qwer'],
            ' 1 2 3 4 5 6 7 8 9 10 11 12 13 14 asdf qwer': [str(i) for i in range(1,15)] + ['asdf qwer'],
            ' 1 2 3 4 5 6 7 8 9 10 11 12 13 14 :asdf qwer': [str(i) for i in range(1,15)] + ['asdf qwer']
        }
        for input, output in cases.iteritems():
            self.assertEqual(output, parse(input, params).captures)

    def test_hostname(self):
        cases = {
            '': False,
            'a': 'a',
            'a-b': 'a-b',
            'a-b.': False,
            'a-b.c': 'a-b.c',
            'a.b-c': 'a.b-c',
            'a-b.c-': 'a-b.c-',  # This looks wrong, but the grammar in RFC2812 allows it
            'a-b.c-d.ef': 'a-b.c-d.ef'
        }
        for input, output in cases.iteritems():
            self.assertEqual(output, parse(input, hostname).parsed)

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
            self.assertEqual(output, parse(input, ip4addr).parsed)

    def test_user(self):
        cases = {
            'a b': False,
            'a\rb': False,
            'a\nb': False,
            'a@b': False,
            'asdf': 'asdf',
            '!#^QWER': '!#^QWER'
        }
        for input, output in cases.iteritems():
            self.assertEqual(output, parse(input, user).parsed)

    def test_message(self):
        out1 = parse('JOIN #a\r\n', message)
        self.assertFalse(out1.named_captures.has_key('prefix'))
        self.assertEqual('JOIN', out1.named_captures['command'])
        self.assertEqual(['#a'], out1.captures)

        out2 = parse(':prefix COMMAND param1 :param is long\r\n', message)
        self.assertEqual('prefix', out2.named_captures['prefix'])
        self.assertEqual('COMMAND', out2.named_captures['command'])
        self.assertEqual(['param1', 'param is long'], out2.captures)
