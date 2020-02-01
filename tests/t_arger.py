import unittest
from mock import patch, call, Mock, MagicMock, DEFAULT
import StringIO

from tests.sert import sert
import src.arger

class TestCheckArgs(unittest.TestCase):

    @patch('sys.stderr', new_callable=StringIO.StringIO) # Mock 'print'
    @patch('sys.exit')
    def test_should_exit_on_bad_arg(self, mock_exit, mock_stdout):
        args = ['--badarg']

        msg = src.arger.check_args(args)

        sert(mock_exit).called_once()


    def test_should_return_default_args(self):
        cmd_args = []

        args = src.arger.check_args(cmd_args)

        sert(len(vars(args).keys())).to_equal(17)
        sert(args.text).is_false()
        sert(args.chars).to_equal(None)
        sert(args.framerate).to_equal(None)
        sert(args.init).to_equal('hpir.ini')
        sert(args.kermit).is_false()
        sert(args.log).to_equal(5)
        sert(args.name).to_equal(None)
        sert(args.get).to_equal(None)
        sert(args.receive).to_equal(None)
        sert(args.send).to_equal(None)
        sert(args.sensitivity).to_equal(None)
        sert(args.serial).is_false()
        sert(args.showinit).is_false()
        sert(args.timeout).to_equal(None)
        sert(args.watchars).to_equal(None)
        sert(args.wavprefix).to_equal(None)
        sert(args.xmodem).is_false()


    def test_should_set_text(self):
        cmd_args = ['--text']

        args = src.arger.check_args(cmd_args)

        sert(args.text).is_true()


    def test_should_set_chars(self):
        cmd_args = ['--serial', '--chars', 'abc']

        args = src.arger.check_args(cmd_args)

        sert(args.chars).to_equal('abc')


    def test_should_set_framerate(self):
        cmd_args = ['--framerate', '200']

        args = src.arger.check_args(cmd_args)

        sert(args.framerate).to_equal(200)


    def test_should_set_init(self):
        cmd_args = ['--init', 'file.txt']

        args = src.arger.check_args(cmd_args)

        sert(args.init).to_equal('file.txt')


    def test_should_set_kermit(self):
        cmd_args = ['--kermit']

        args = src.arger.check_args(cmd_args)

        sert(args.kermit).is_true()


    def test_should_set_log(self):
        sert(src.arger.check_args(['-l']).log).to_equal(6)
        sert(src.arger.check_args(['-ll']).log).to_equal(7)
        sert(src.arger.check_args(['-lll']).log).to_equal(8)
        sert(src.arger.check_args(['-llll']).log).to_equal(9)
        sert(src.arger.check_args(['-lllll']).log).to_equal(10)


    def test_should_set_name(self):
        cmd_args = ['--name', 'foo']

        args = src.arger.check_args(cmd_args)

        sert(args.name).to_equal('foo')


    def test_should_set_receive(self):
        cmd_args = ['--receive', 'bar']

        args = src.arger.check_args(cmd_args)

        sert(args.receive).to_equal('bar')


    def test_should_set_send(self):
        cmd_args = ['--send', 'baz']

        args = src.arger.check_args(cmd_args)

        sert(args.send).to_equal('baz')


    def test_should_set_sensitivity(self):
        cmd_args = ['--sensitivity', '0.4']

        args = src.arger.check_args(cmd_args)

        sert(args.sensitivity).to_equal(0.4)


    def test_should_set_serial(self):
        cmd_args = ['--serial']

        args = src.arger.check_args(cmd_args)

        sert(args.serial).is_true()


    def test_should_set_showinit(self):
        cmd_args = ['--showinit']

        args = src.arger.check_args(cmd_args)

        sert(args.showinit).is_true()


    def test_should_set_timeout(self):
        cmd_args = ['--serial', '--timeout', '30']

        args = src.arger.check_args(cmd_args)

        sert(args.timeout).to_equal(30)


    def test_should_set_watchars(self):
        cmd_args = ['--serial', '--watchars', 'XYZ']

        args = src.arger.check_args(cmd_args)

        sert(args.watchars).to_equal('XYZ')


    def test_should_set_wavprefix(self):
        cmd_args = ['--wavprefix', 'boz']

        args = src.arger.check_args(cmd_args)

        sert(args.wavprefix).to_equal('boz')


    def test_should_set_xmodem(self):
        cmd_args = ['--xmodem']

        args = src.arger.check_args(cmd_args)

        sert(args.xmodem).is_true()


class TestAddHelpGroup(unittest.TestCase):

    def test_should_ignore_optionals(self):
        parser = src.arger._get_common_parser()
        src.arger.optionals = None
        sert(len(parser._action_groups)).to_equal(1)

        src.arger._add_help_group(parser)

        sert(len(parser._action_groups)).to_equal(1)
