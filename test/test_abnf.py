import unittest
from abnf import *

class AbnfTest(unittest.TestCase):
    """
    def test_nickname(self):
        self.assertFalse(parse('333', nickname))
        self.assertEqual('abcd', parse('abcd', nickname))
        self.assertEqual('[]\`_^{|}', parse('[]\`_^{|}', nickname))

    def test_command(self):
        self.assertFalse(parse('1', command))
        self.assertFalse(parse('11', command))
        self.assertEqual('100', parse('100', command))

        self.assertFalse(parse('2fo', command))
        self.assertFalse(parse('foo2', command))

        self.assertEqual('fooBAR', parse('fooBAR', command))
    """

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
            print input
            self.assertEqual(output, parse(input, params))

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
            self.assertEqual(output, parse(input, hostname))

            """
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
            self.assertEqual(output, parse(input, ip4addr))

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
            self.assertEqual(output, parse(input, user))

    def test_join(self):
        cases = {
            'JOIN #a\r\n': ('JOIN', '#a'),
            'JOIN #a \r\n': ('JOIN', '#a')
        }
        for input, output in cases.iteritems():
            msg = parse(input, message)
            if not msg:
                self.fail()
            self.assertEqual(output[0], msg['command'])
            self.assertEqual([output[1]], msg['params'])
                        """