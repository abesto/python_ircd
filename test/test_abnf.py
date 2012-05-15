import unittest

import abnf
import config


class AbnfTest(unittest.TestCase):
    def setUp(self):
        config.traling_spaces = False
        config.soft_eol = False
        reload(abnf)

    def test_nickname(self):
        self.assertFalse(abnf.parse('333', abnf.nickname).parsed)
        self.assertEqual('abcd', abnf.parse('abcd', abnf.nickname).parsed)
        self.assertEqual('[]\`_^{|}', abnf.parse('[]\`_^{|}', abnf.nickname).parsed)

    def test_command(self):
        self.assertFalse(abnf.parse('1', abnf.command).parsed)
        self.assertFalse(abnf.parse('11', abnf.command).parsed)
        self.assertEqual('100', abnf.parse('100', abnf.command).parsed)

        self.assertFalse(abnf.parse('2fo', abnf.command).parsed)
        self.assertFalse(abnf.parse('foo2', abnf.command).parsed)

        self.assertEqual('fooBAR', abnf.parse('fooBAR', abnf.command).parsed)

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
            self.assertEqual(output, abnf.parse(input, abnf.params).captures)

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
            self.assertEqual(output, abnf.parse(input, abnf.hostname).parsed)

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
            self.assertEqual(output, abnf.parse(input, abnf.ip4addr).parsed)

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
            self.assertEqual(output, abnf.parse(input, abnf.user).parsed)

    def test_message(self):
        out1 = abnf.parse('JOIN #a\r\n', abnf.message)
        self.assertFalse(out1.has_key('prefix'))
        self.assertEqual('JOIN', out1['command'])
        self.assertEqual(['#a'], out1.captures)

        out2 = abnf.parse(':prefix COMMAND param1 :param is long\r\n', abnf.message)
        self.assertEqual('prefix', out2['prefix'])
        self.assertEqual('COMMAND', out2['command'])
        self.assertEqual(['param1', 'param is long'], out2.captures)


    def test_trailing_spaces(self):
        self.assertFalse(abnf.parse('JOIN #a \r\n', abnf.message).parsed)
        config.traling_spaces = True
        reload(abnf)
        out = abnf.parse('JOIN #a   \r\n', abnf.message)
        self.assertFalse(out.has_key('prefix'))
        self.assertEqual('JOIN', out['command'])
        self.assertEqual(['#a'], out.captures)

    def test_soft_eol(self):
        self.assertFalse(abnf.parse('JOIN #a\r', abnf.message).parsed)
        self.assertFalse(abnf.parse('JOIN #a\n', abnf.message).parsed)
        config.soft_eol = True
        reload(abnf)
        out1 = abnf.parse('JOIN #a\r', abnf.message)
        self.assertFalse(out1.has_key('prefix'))
        self.assertEqual('JOIN', out1['command'])
        self.assertEqual(['#a'], out1.captures)
        out2 = abnf.parse('JOIN #a\n', abnf.message)
        self.assertFalse(out2.has_key('prefix'))
        self.assertEqual('JOIN', out2['command'])
        self.assertEqual(['#a'], out2.captures)

    def test_trailing_spaces_and_soft_eol(self):
        config.soft_eol = True
        config.traling_spaces = True
        reload(abnf)
        out = abnf.parse('JOIN #a   \r', abnf.message)
        self.assertFalse(out.has_key('prefix'))
        self.assertEqual('JOIN', out['command'])
        self.assertEqual(['#a'], out.captures)

