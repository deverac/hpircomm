import unittest
import subprocess
from mock import patch #, call, Mock, MagicMock, DEFAULT
from tests.sert import sert

import StringIO
import sys
import hpir


def gen_args(arg0, incompat_args):
    args = []
    for arg in incompat_args:
        args.append([arg0, arg])
    return args


def get_incompat_xmodem_args():
    return gen_args('--xmodem', [
        '--serial',
        '--kermit',
        '--text',
        '-n abc',
        '--name abc',
        '-c abc',
        '--chars abc',
        '-t 9',
        '--timeout 9',
        '-w AA',
        '--watchars AA',
        '--get abc',
    ])


def get_incompat_kermit_args():
    return gen_args('--kermit', [
        '--xmodem',
        '--serial',
        '-c abc',
        '--chars abc',
        '-t 9',
        '--timeout 9',
        '-w AA',
        '--watchars AA',
    ])


def get_incompat_serial_args():
    return gen_args('--serial', [
        '--kermit',
        '--xmodem',
        '--text',
        '-n abc',
        '--name abc',
        '--get abc',
    ])



class TestHpir(unittest.TestCase):


    @patch('sys.exit')
    @patch('src.hpcomm')
    @patch('sys.stderr', new_callable=StringIO.StringIO) # Mock 'print'
    def test_should_error_with_incompatible_args(self, mock_print, mock_hpcomm, mock_exit):
        incompat_args = []
        incompat_args.extend(get_incompat_xmodem_args())
        incompat_args.extend(get_incompat_kermit_args())
        incompat_args.extend(get_incompat_serial_args())

        for incompat_arg in incompat_args:
            sys_argv = ['hpir.py']
            sys_argv.extend(incompat_arg)
            mock_exit.reset_mock()
            sert(mock_exit).not_called()

            res2 = hpir.run_main(sys_argv)

            if len(mock_exit.mock_calls) == 0:
                # No calls were made. Display the args that failed.
                print('Testing args {}'.format(sys_argv))
            sert(mock_exit).called_once_with(2)


    @patch('sys.exit')
    @patch('src.hpcomm')
    @patch('sys.stdout', new_callable=StringIO.StringIO) # Mock 'print'
    def test_should_show_help(self, mock_print, mock_hpcomm, mock_exit):
        incompat_args = [['-h'], ['--help']]

        for incompat_arg in incompat_args:
            sys_argv = ['hpir.py']
            sys_argv.extend(incompat_arg)
            mock_exit.reset_mock()
            sert(mock_exit).not_called()

            res2 = hpir.run_main(sys_argv)

            # Spot-check
            sert('usage:' in mock_print.getvalue()).is_true()
            sert('protocol:' in mock_print.getvalue()).is_true()
            sert('file:' in mock_print.getvalue()).is_true()
            sert('kermit:' in mock_print.getvalue()).is_true()
            sert('serial:' in mock_print.getvalue()).is_true()
            sert('config:' in mock_print.getvalue()).is_true()
            sert('help:' in mock_print.getvalue()).is_true()
            sert(mock_exit).called_once_with(0)
