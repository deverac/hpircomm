import unittest
from mock import patch, call, Mock, MagicMock, DEFAULT

import src.log
import src.transport
import src.dispatcher

from tests.sert import sert, TAttrBag


def targs(**kwargs):
    default_dct = {
        'init': None,
        'showinit': True,
        'wavprefix': None,
        'framerate': 14400,
        'sensitivity': 0.11,
        'kermit': None,
        'serial': None,
        'xmodem': None,
        'send': None,
        'receive': None,
        'text': False,
        'get': None,
        'name': None,
        'chars': None,
        'timeout':  None,
        'watchars': None,
    }
    default_dct.update(kwargs)
    return TAttrBag(**default_dct)



class TestReadScripts(unittest.TestCase):

    @patch('__builtin__.open')
    def test_should_read_a_script(self, mock_open):
        mock_open.return_value.readlines.return_value = ['some text\n', 'more text']

        scripts = src.dispatcher.read_scripts('a.txt')

        sert(scripts).to_equal(['some text', 'more text'])


    @patch('__builtin__.open')
    def test_should_read_multiple_scripts(self, mock_open):
        mock_open.return_value.readlines.side_effect = [['some text\n', 'more text'], ['extra text\n', 'other text']]

        scripts = src.dispatcher.read_scripts('a.txt b.txt')

        sert(scripts).to_equal(['extra text', 'other text', 'some text', 'more text'])



class TestSerialCmdsExecLine(unittest.TestCase):

    sc = None

    @patch('src.serial.Serial')
    def setUp(self, mock_serial):
        global sc
        sc = src.dispatcher.SerialCmds(Mock())


    def test_should_send_file(self):
        sc.exec_line('send file abc.txt')
        sert(sc.serial.send_file).called_once_with('abc.txt')


    def test_should_send_chars(self):
        sc.exec_line('send chars some text')
        sert(sc.serial.send_chars).called_once_with('some text')


    @patch('src.log.i')
    def test_should_handle_invalid_send(self, mock_i):
        sc.exec_line('send invalid_text')
        sert(mock_i).called_once_with('Invalid send: invalid_text')


    def test_should_receive_file(self):
        sc.exec_line('receive file.txt')
        sert(sc.serial.receive_file).called_once_with('file.txt')


    def test_should_show_config(self):
        sc.exec_line('show ab cd ef')
        sert(sc.serial.show_config).called_once_with('ab cd ef')


    def test_should_set_config(self):
        sc.exec_line('set ab cd ef')
        sert(sc.serial.set_config).called_once_with('ab cd ef')


    def test_should_show_help(self):
        sc.exec_line('help')
        sert(sc.serial.help).called_once_with('')


    def test_should_show_help_param(self):
        sc.exec_line('help abc')
        sert(sc.serial.help).called_once_with('abc')


    @patch('src.log.i')
    def test_should_log_bad_command(self, mock_i):
        sc.exec_line('bad-cmd abc')
        sert(mock_i).called_once_with('Invalid bad-cmd abc')



class TestXmodemCmdsExecLine(unittest.TestCase):

    xc = None

    @patch('src.xmodem.Xmodem')
    def setUp(self, mock_xmodem):
        global xc
        xc = src.dispatcher.XmodemCmds(Mock())


    def test_should_send_file(self):
        xc.exec_line('send file.txt')
        sert(xc.xmodem.send_file).called_once_with('file.txt')


    def test_should_receive_file(self):
        xc.exec_line('receive file.txt')
        sert(xc.xmodem.receive_file).called_once_with('file.txt')


    def test_should_show_config(self):
        xc.exec_line('show ab cd ef')
        sert(xc.xmodem.show_config).called_once_with('ab cd ef')


    def test_should_set_config(self):
        xc.exec_line('set ab cd ef')
        sert(xc.xmodem.set_config).called_once_with('ab cd ef')


    def test_should_show_help(self):
        xc.exec_line('help')
        sert(xc.xmodem.help).called_once_with('')


    def test_should_show_help_param(self):
        xc.exec_line('help abc')
        sert(xc.xmodem.help).called_once_with('abc')


    @patch('src.log.i')
    def test_should_log_bad_command(self, mock_i):
        xc.exec_line('bad-cmd abc')
        sert(mock_i).called_once_with('Invalid command bad-cmd abc')



class TestKermitCmdsExecLine(unittest.TestCase):

    kc = None

    @patch('src.kermit.Kermit')
    def setUp(self, mock_kermit):
        global kc
        kc = src.dispatcher.KermitCmds(Mock())
        kc.kermit = Mock()
        kc.kermit.next_cmd.return_value = ''


    def test_should_call_help(self):
        kc.exec_line('help')
        sert(kc.kermit.help).called_once_with('')


    def test_should_call_finish(self):
        kc.exec_line('finish')
        sert(kc.kermit.finish).called_once_with()


    def test_should_call_send(self):
        kc.exec_line('send abc def')
        sert(kc.kermit.send).called_once_with('abc def')


    def test_should_call_get(self):
        kc.exec_line('get abc def')
        sert(kc.kermit.get).called_once_with('abc def')


    def test_should_call_receive(self):
        kc.exec_line('receive')
        sert(kc.kermit.receive).called_once_with()


    def test_should_call_remote_cwd(self):
        kc.exec_line('remote cwd abc')
        sert(kc.kermit.remote_cwd).called_once_with('abc')


    def test_should_call_remote_delete(self):
        kc.exec_line('remote delete abc def')
        sert(kc.kermit.remote_delete).called_once_with('abc def')


    def test_should_call_remote_directory(self):
        kc.exec_line('remote directory abc def')
        sert(kc.kermit.remote_directory).called_once_with()


    def test_should_call_remote_host(self):
        kc.exec_line('remote host abc def')
        sert(kc.kermit.remote_host).called_once_with('abc def')


    @patch('__builtin__.raw_input')
    @patch('src.log.i')
    def test_should_call_remote_host_with_no_args(self, mock_i, mock_input):
        mock_input.return_value = 'abcde'
        kc.kermit.send_command = Mock(side_effect = [KeyboardInterrupt()])

        kc.exec_line('remote host')

        sert(mock_i).called_twice()
        sert(mock_i).first_call_called_with('Press Ctrl-C to quit')
        sert(mock_i).second_call_called_with('')
        sert(kc.kermit.send_command).called_once_with('abcde')
        sert(mock_input).called_with('hpcalc> ')


    def test_should_call_remote_path(self):
        kc.exec_line('remote path')
        sert(kc.kermit.remote_path).called_once_with()


    def test_should_call_remote_space(self):
        kc.exec_line('remote space')
        sert(kc.kermit.remote_space).called_once_with()


    def test_should_call_remote_type(self):
        kc.exec_line('remote type abc def')
        sert(kc.kermit.remote_type).called_once_with('abc def')


    @patch('src.log.i')
    def test_should_handle_invalid_remote_command(self, mock_i):
        kc.exec_line('remote bad-command')
        sert(mock_i).called_once_with('Invalid remote command: bad-command')


    def test_should_call_server(self):
        kc.exec_line('server')
        sert(kc.kermit.server).called_once_with('')


    def test_should_call_server_with_param(self):
        kc.exec_line('server abc')
        sert(kc.kermit.server).called_once_with('abc')


    def test_should_call_take(self):
        kc.exec_line('take abc')
        sert(kc.kermit.take).called_once_with('abc')


    def test_should_call_echo(self):
        kc.exec_line('echo abc')
        sert(kc.kermit.echo).called_once_with('abc')


    def test_should_call_local_cwd(self):
        kc.exec_line('local cwd abc')
        sert(kc.kermit.local_cwd).called_once_with('abc')


    def test_should_call_local_delete(self):
        kc.exec_line('local delete abc def')
        sert(kc.kermit.local_delete).called_once_with('abc def')


    def test_should_call_local_directory(self):
        kc.exec_line('local directory abc def')
        sert(kc.kermit.local_directory).called_once_with('abc def')


    def test_should_call_local_path(self):
        kc.exec_line('local path')
        sert(kc.kermit.local_path).called_once_with()


    def test_should_call_local_push(self):
        kc.exec_line('local push')
        sert(kc.kermit.local_push).called_once_with()


    def test_should_call_local_run(self):
        kc.exec_line('local run abc def')
        sert(kc.kermit.local_run).called_once_with('abc def')


    def test_should_call_local_space(self):
        kc.exec_line('local space')
        sert(kc.kermit.local_space).called_once_with()


    def test_should_call_local_type(self):
        kc.exec_line('local type abc def')
        sert(kc.kermit.local_type).called_once_with('abc def')


    @patch('src.log.i')
    def test_should_handle_invalid_local_command(self, mock_i):
        kc.exec_line('local bad-command')
        sert(mock_i).called_once_with('Invalid local command: bad-command')


    def test_should_call_cwd_without_local(self):
        kc.exec_line('cwd abc')
        sert(kc.kermit.local_cwd).called_once_with('abc')


    def test_should_call_delete_without_local(self):
        kc.exec_line('delete abc def')
        sert(kc.kermit.local_delete).called_once_with('abc def')


    def test_should_call_directory_without_local(self):
        kc.exec_line('directory abc def')
        sert(kc.kermit.local_directory).called_once_with('abc def')


    def test_should_call_path_without_local(self):
        kc.exec_line('path')
        sert(kc.kermit.local_path).called_once_with()


    def test_should_call_push_without_local(self):
        kc.exec_line('push')
        sert(kc.kermit.local_push).called_once_with()


    def test_should_call_run_without_local(self):
        kc.exec_line('run abc def')
        sert(kc.kermit.local_run).called_once_with('abc def')


    def test_should_call_space_without_local(self):
        kc.exec_line('space')
        sert(kc.kermit.local_space).called_once_with()


    def test_should_call_type_without_local(self):
        kc.exec_line('type abc def')
        sert(kc.kermit.local_type).called_once_with('abc def')


    def test_should_call_set(self):
        kc.exec_line('set abc def')
        sert(kc.kermit.set).called_once_with('abc def')


    def test_should_call_show(self):
        kc.exec_line('show abc def')
        sert(kc.kermit.show).called_once_with('abc def')


    def test_should_call_show(self):
        kc.exec_line('show abc def')
        sert(kc.kermit.show).called_once_with('abc def')


    def test_should_call_local_when_no_match_parsing_line(self):
        kc.exec_line('dir abc')
        sert(kc.kermit.local_directory).called_once_with('abc')


    @patch('src.dispatcher.log')
    def test_should_skip_local_when_error_parsing_line(self, mock_log):
        kc.exec_line('s')
        sert(mock_log.e).called_once_with('Multiple matches for "s". Matches: [\'send\', \'server\', \'set\', \'show\']')


class TestDispatcherInit(unittest.TestCase):

    @patch('__builtin__.open')
    @patch('src.log.i')
    def test_should_read_ini_script(self, mock_i, mock_open):
        mock_open.return_value.readlines.return_value = ['some text\n', 'more text']

        d = src.dispatcher.Dispatcher(targs(init='abc.ini'))

        sert(mock_i).called_once_with('Reading init script abc.ini')
        sert(d.scripts).to_equal(['some text', 'more text'])


    @patch('__builtin__.open')
    @patch('src.log.e')
    @patch('src.log.i')
    def test_should_handle_read_ini_error(self, mock_i, mock_e, mock_open):
        mock_open.side_effect=IOError('bad thing')

        d = src.dispatcher.Dispatcher(targs(init='abc.ini'))

        sert(mock_i).called_once_with('Reading init script abc.ini')
        sert(mock_e).called_once_with('Error reading abc.ini')



class TestDispatcherProcArgs(unittest.TestCase):

    def test_should_handle_serial_args(self):
        d = src.dispatcher.Dispatcher()
        sert(d.proc_args(targs(serial=True, receive='abc.txt'))).to_equal(['serial receive abc.txt', 'quit'])
        sert(d.proc_args(targs(serial=True, receive='abc.txt', timeout=5))).to_equal(['serial set mode timeout', 'serial set timeout 5', 'serial receive abc.txt', 'quit'])
        sert(d.proc_args(targs(serial=True, receive='abc.txt', watchars='AA'))).to_equal(['serial set mode watchars', 'serial set watchars AA', 'serial receive abc.txt', 'quit'])
        sert(d.proc_args(targs(serial=True, send='abc.txt'))).to_equal(['serial send file abc.txt', 'quit'])
        sert(d.proc_args(targs(serial=True, chars='jkl'))).to_equal(['serial send chars jkl', 'quit'])


    def test_should_handle_xmodem_args(self):
        d = src.dispatcher.Dispatcher()
        sert(d.proc_args(targs(xmodem=True, send='abc.txt'))).to_equal(['xmodem send abc.txt', 'quit'])
        sert(d.proc_args(targs(xmodem=True, receive='abc.txt'))).to_equal(['xmodem receive abc.txt', 'quit'])


    def test_should_handle_kermit_args(self):
        d = src.dispatcher.Dispatcher()
        sert(d.proc_args(targs(kermit=True, send='abc.txt'))).to_equal(['kermit send abc.txt', 'quit'])
        sert(d.proc_args(targs(kermit=True, send='abc.txt', text=True))).to_equal(['kermit set transfer text', 'kermit send abc.txt', 'quit'])
        sert(d.proc_args(targs(kermit=True, send='abc.txt', text=True, name='B'))).to_equal(['kermit set transfer text', 'kermit send abc.txt as B', 'quit'])
        sert(d.proc_args(targs(kermit=True, receive='abc.txt'))).to_equal(['kermit receive abc.txt', 'quit'])
        sert(d.proc_args(targs(kermit=True, get='abc.txt'))).to_equal(['kermit get abc.txt', 'quit'])


    def test_should_handle_missing_kermit_args(self):
        d = src.dispatcher.Dispatcher()
        sert(d.proc_args(targs(send='abc.txt'))).to_equal(['kermit send abc.txt', 'quit'])
        sert(d.proc_args(targs(send='abc.txt', text=True))).to_equal(['kermit set transfer text', 'kermit send abc.txt', 'quit'])
        sert(d.proc_args(targs(send='abc.txt', text=True, name='B'))).to_equal(['kermit set transfer text', 'kermit send abc.txt as B', 'quit'])
        sert(d.proc_args(targs(receive='abc.txt'))).to_equal(['kermit receive abc.txt', 'quit'])
        sert(d.proc_args(targs(get='abc.txt'))).to_equal(['kermit get abc.txt', 'quit'])


    def test_should_handle_single_protocol_args(self):
        d = src.dispatcher.Dispatcher()
        sert(d.proc_args(targs(serial=True))).to_equal(['serial'])
        sert(d.proc_args(targs(kermit=True))).to_equal(['kermit'])
        sert(d.proc_args(targs(xmodem=True))).to_equal(['xmodem'])



class TestDispatcherStartTransport(unittest.TestCase):

    def test_should_start_transport(self):
        d = src.dispatcher.Dispatcher()
        d.transport = Mock()

        cmd = d.start_transport()

        sert(d.transport.start_it).called_once()



class TestDispatcherStopTransport(unittest.TestCase):

    def test_should_stop_transport(self):
        d = src.dispatcher.Dispatcher()
        d.transport = Mock()

        cmd = d.stop_transport()

        sert(d.transport.stop_it).called_once()



class TestDispatcherNextScriptCmd(unittest.TestCase):

    def test_should_get_next_cmd(self):
        d = src.dispatcher.Dispatcher()
        d.scripts = ['some text', 'more text']

        cmd = d.next_script_cmd()

        sert(cmd).to_equal('some text')

        cmd = d.next_script_cmd()

        sert(cmd).to_equal('more text')


    def test_should_execute_script_and_arg_cmds(self):
        d = src.dispatcher.Dispatcher()
        d.scripts = ['some text', 'more text']
        d.arg_cmds = ['aa', 'bb']

        cmd = d.next_script_cmd()

        sert(cmd).to_equal('some text')

        cmd = d.next_script_cmd()

        sert(cmd).to_equal('more text')

        cmd = d.next_script_cmd()

        sert(cmd).to_equal('aa')

        cmd = d.next_script_cmd()

        sert(cmd).to_equal('bb')


    def test_should_clear_arg_flag(self):
        d = src.dispatcher.Dispatcher()
        d.scripts = ['some text']
        d.arg_cmds = ['aa']
        d.cmd_proc = d.xmodem_cmd_proc

        cmd = d.next_script_cmd()

        sert(d.arg_flag).is_true()

        cmd = d.next_script_cmd()

        sert(d.arg_flag).is_false()


    def test_should_clear_cmd_proc(self):
        d = src.dispatcher.Dispatcher()
        d.scripts = ['some text']
        d.arg_cmds = ['aa']
        d.cmd_proc = d.xmodem_cmd_proc

        cmd = d.next_script_cmd()

        sert(d.cmd_proc).not_equal(None)

        cmd = d.next_script_cmd()

        sert(d.cmd_proc).to_equal(None)


    def test_should_quit(self):
        d = src.dispatcher.Dispatcher()
        d.scripts = ['some text']
        d.arg_cmds = ['aa']
        d.cmd_proc = d.xmodem_cmd_proc
        d.quit = Mock()

        cmd = d.next_script_cmd()

        sert(d.quit).not_called()

        cmd = d.next_script_cmd()

        sert(d.quit).called_once()



class TestDispatcherListen(unittest.TestCase):

    @patch('time.sleep')
    def test_should_listen_with_default_values(self, mock_sleep):
        count = 30
        dur = 1.0
        d = src.dispatcher.Dispatcher()
        d.transport = MagicMock()

        d.listen()

        sert(mock_sleep).called_n_times(count)
        for i in range(1, count+1):
            sert(mock_sleep).nth_call_called_with(i, dur)
        sert(d.transport.peek).called_n_times(count)


    @patch('time.sleep')
    def test_should_listen_with_supplied_values(self, mock_sleep):
        count = 10
        dur = 3.0
        d = src.dispatcher.Dispatcher()
        d.transport = MagicMock()

        d.listen('{} {}'.format(count, dur))

        sert(mock_sleep).called_n_times(count)
        for i in range(1, count+1):
            sert(mock_sleep).nth_call_called_with(i, dur)
        sert(d.transport.peek).called_n_times(count)



class TestDispatcherPeek(unittest.TestCase):

    @patch('src.log.i')
    def test_should_peek(self, mock_i):
        d = src.dispatcher.Dispatcher()
        d.transport = Mock()

        d.peek()

        sert(d.transport.peek).called_once()
        sert(mock_i).called_once()


class TestDispatcherWait(unittest.TestCase):

    @patch('time.sleep')
    @patch('src.log.i')
    def test_should_wait_with_default_value(self, mock_i, mock_sleep):
        default_secs = 10.0
        d = src.dispatcher.Dispatcher()

        d.wait()

        sert(mock_sleep).called_once_with(default_secs)
        sert(mock_i).called_once_with('Waiting for {} seconds'.format(default_secs))


    @patch('time.sleep')
    @patch('src.log.i')
    def test_should_wait_with_supplied_value(self, mock_i, mock_sleep):
        secs = 4.5
        d = src.dispatcher.Dispatcher()

        d.wait('{}'.format(secs))

        sert(mock_sleep).called_once_with(secs)
        sert(mock_i).called_once_with('Waiting for {} seconds'.format(secs))



class TestDispatcherSetConfig(unittest.TestCase):

    def test_should_set_config_value(self):
        d = src.dispatcher.Dispatcher()
        key = 'trace-on-error'
        sert(d.config[key].value).is_true()

        d.set_config('{} false'.format(key))

        sert(d.config[key].value).is_false()


    def test_should_set_wav_prefix(self):
        d = src.dispatcher.Dispatcher()
        d.transport = Mock()
        key = 'wav-prefix'
        val = 'abc'

        d.set_config('{} {}'.format(key, val))

        sert(d.transport.set_wav_prefix).called_once_with(val)


    @patch('src.log.set_log_level')
    def test_should_set_log_level(self, mock_level):
        d = src.dispatcher.Dispatcher()
        key = 'log-level'
        val = 2

        d.set_config('{} {}'.format(key, val))

        sert(mock_level).called_once_with(val)



class TestDispatcherShowConfig(unittest.TestCase):

    @patch('src.log.i')
    def test_should_show_config(self, mock_i):
        d = src.dispatcher.Dispatcher()

        d.show_config('')

        sert(mock_i).called_n_times(5)
        sert(mock_i).nth_call_called_with(1, '  exit-on-error : false')
        sert(mock_i).nth_call_called_with(2, '  local-echo    : true')
        sert(mock_i).nth_call_called_with(3, '  log-level     : 5')
        sert(mock_i).nth_call_called_with(4, '  trace-on-error: true')
        sert(mock_i).nth_call_called_with(5, '  wav-prefix    : ')


    @patch('src.log.i')
    def test_should_show_single_config(self, mock_i):
        d = src.dispatcher.Dispatcher()

        d.show_config('local-e')

        sert(mock_i).called_once_with('  local-echo: true')



class TestDispatcherEcho(unittest.TestCase):

    @patch('src.log.i')
    def test_should_echo(self, mock_i):
        txt = 'some text'
        d = src.dispatcher.Dispatcher()

        d.echo(txt)

        sert(mock_i).called_once_with(txt)



class TestDispatcherHelp(unittest.TestCase):

    @patch('src.log.i')
    def test_should_help(self, mock_i):
        d = src.dispatcher.Dispatcher()

        d.help()

        sert(mock_i).called_n_times(19)
        # Spot check
        sert(mock_i).nth_call_called_with(3, '  local-echo    : Echo command line locally {false, true}')
        sert(mock_i).nth_call_called_with(11, '  listen [COUNT [SECS]]: Listen for incoming data (30 1)')



class TestDispatcherProcSerial(unittest.TestCase):

    def test_should_execute_cmd(self):
        d = src.dispatcher.Dispatcher()
        d.serial_cmd_proc = Mock()
        cmd = 'ab cd'

        d.proc_serial(cmd)

        sert(d.serial_cmd_proc.exec_line).called_with(cmd)


    def test_should_set_proc_and_prompt(self):
        d = src.dispatcher.Dispatcher()
        sert(d.prompt).to_equal('> ')
        sert(d.cmd_proc).to_equal(None)

        d.proc_serial()

        sert(d.prompt).to_equal('serial> ')
        sert(d.cmd_proc).to_equal(d.serial_cmd_proc)



class TestDispatcherProcKermit(unittest.TestCase):

    def test_should_execute_cmd(self):
        d = src.dispatcher.Dispatcher()
        d.kermit_cmd_proc = Mock()
        cmd = 'ab cd'

        d.proc_kermit(cmd)

        sert(d.kermit_cmd_proc.exec_line).called_with(cmd)


    def test_should_set_proc_and_prompt(self):
        d = src.dispatcher.Dispatcher()
        sert(d.prompt).to_equal('> ')
        sert(d.cmd_proc).to_equal(None)

        d.proc_kermit()

        sert(d.prompt).to_equal('kermit> ')
        sert(d.cmd_proc).to_equal(d.kermit_cmd_proc)



class TestDispatcherProcXmodem(unittest.TestCase):

    def test_should_execute_cmd(self):
        d = src.dispatcher.Dispatcher()
        d.xmodem_cmd_proc = Mock()
        cmd = 'ab cd'

        d.proc_xmodem(cmd)

        sert(d.xmodem_cmd_proc.exec_line).called_with(cmd)


    def test_should_set_proc_and_prompt(self):
        d = src.dispatcher.Dispatcher()
        sert(d.prompt).to_equal('> ')
        sert(d.cmd_proc).to_equal(None)

        d.proc_xmodem()

        sert(d.prompt).to_equal('xmodem> ')
        sert(d.cmd_proc).to_equal(d.xmodem_cmd_proc)



class TestDispatcherScript(unittest.TestCase):

    @patch('__builtin__.open')
    def test_should_populate_scripts(self, mock_open):
        mock_open.return_value.readlines.return_value = ['some text\n', 'more text']
        d = src.dispatcher.Dispatcher()

        d.script('a.txt')

        sert(d.scripts).to_equal(['some text', 'more text'])



class TestDispatcherQuit(unittest.TestCase):

    d = None

    def setUp(self):
        global d
        d = src.dispatcher.Dispatcher()


    def test_should_set_done_flag(self):
        sert(d.done).is_false()

        d.quit()

        sert(d.done).is_true()


    def test_should_reset_prompt(self):
        d.proc_serial()
        sert(d.prompt).to_equal('serial> ')

        d.quit()

        sert(d.prompt).to_equal('> ')


    def test_should_reset_cmd_proc(self):
        d.proc_serial()
        sert(d.prompt).not_equal(None)

        d.quit()

        sert(d.cmd_proc).to_equal(None)



class TestDispatcherIsDone(unittest.TestCase):

    def test_should_return_true_value(self):
        d = src.dispatcher.Dispatcher()
        d.done = True

        ans = d.is_done()

        sert(ans).is_true()


    def test_should_return_false_value(self):
        d = src.dispatcher.Dispatcher()
        d.done = False

        ans = d.is_done()

        sert(ans).is_false()



class TestDispatcherForceDone(unittest.TestCase):

    def test_should_set_value_true_value(self):
        d = src.dispatcher.Dispatcher()
        d.done = False

        d.force_done()

        sert(d.done).is_true()



class TestDispatcherReadLine(unittest.TestCase):

    @patch('src.log.i')
    def test_should_read_line_from_script(self, mock_i):
        d = src.dispatcher.Dispatcher()
        d.config['local-echo'].value = True
        d.scripts = ['abc', 'def']

        res = d.read_line()

        sert(res).to_equal('abc')
        sert(mock_i).called_once_with('=> abc')


    @patch('__builtin__.raw_input')
    def test_should_read_line_from_raw_input(self, mock_input):
        mock_input.return_value = 'a cmd'
        d = src.dispatcher.Dispatcher()
        d.config['local-echo'].value = True
        d.scripts = []

        res = d.read_line()

        sert(res).to_equal('a cmd')


    @patch('__builtin__.raw_input')
    def test_should_handle_eoferror(self, mock_input):
        mock_input.side_effect = ['cmd', EOFError('bad')]
        d = src.dispatcher.Dispatcher()
        d.config['local-echo'].value = True
        d.scripts = []

        res = d.read_line()

        sert(res).to_equal('cmd')

        res = d.read_line()

        sert(res).to_equal('')



class TestDispatcherExecLine(unittest.TestCase):

    def test_should_strip_line(self):
        d = src.dispatcher.Dispatcher()
        line = Mock()
        line.strip.return_value = ''

        d.exec_line(line)

        sert(line.strip).called_once()


    def test_should_call_quit(self):
        d = src.dispatcher.Dispatcher()
        d.quit = Mock()

        d.exec_line('quit')

        sert(d.quit).called_once()


    def test_should_call_subproc(self):
        d = src.dispatcher.Dispatcher()
        d.cmd_proc = Mock()

        d.exec_line('ab cd ef')

        sert(d.cmd_proc.exec_line).called_once_with('ab cd ef')


    def test_should_call_echo(self):
        d = src.dispatcher.Dispatcher()
        d.echo = Mock()

        d.exec_line('echo abc')

        sert(d.echo).called_once_with('abc')


    def test_should_call_proc_serial(self):
        d = src.dispatcher.Dispatcher()
        d.proc_serial = Mock()

        d.exec_line('serial a scmd')

        sert(d.proc_serial).called_once_with('a scmd')


    def test_should_call_proc_kermit(self):
        d = src.dispatcher.Dispatcher()
        d.proc_kermit = Mock()

        d.exec_line('kermit a kcmd')

        sert(d.proc_kermit).called_once_with('a kcmd')


    def test_should_call_proc_xmodem(self):
        d = src.dispatcher.Dispatcher()
        d.proc_xmodem = Mock()

        d.exec_line('xmodem a xcmd')

        sert(d.proc_xmodem).called_once_with('a xcmd')


    def test_should_call_help(self):
        d = src.dispatcher.Dispatcher()
        d.help = Mock()

        d.exec_line('help')

        sert(d.help).called_once()


    def test_should_call_listen(self):
        d = src.dispatcher.Dispatcher()
        d.listen = Mock()

        d.exec_line('listen 4 5')

        sert(d.listen).called_once_with('4 5')


    def test_should_call_peek(self):
        d = src.dispatcher.Dispatcher()
        d.peek = Mock()

        d.exec_line('peek')

        sert(d.peek).called_once()


    def test_should_call_wait(self):
        d = src.dispatcher.Dispatcher()
        d.wait = Mock()

        d.exec_line('wait 15')

        sert(d.wait).called_once_with('15')


    def test_should_call_script(self):
        d = src.dispatcher.Dispatcher()
        d.script = Mock()

        d.exec_line('script abc.txt')

        sert(d.script).called_once_with('abc.txt')


    def test_should_call_show_config(self):
        d = src.dispatcher.Dispatcher()
        d.show_config = Mock()

        d.exec_line('show ab cd')

        sert(d.show_config).called_once_with('ab cd')


    def test_should_call_set_config(self):
        d = src.dispatcher.Dispatcher()
        d.set_config = Mock()

        d.exec_line('set wx yz')

        sert(d.set_config).called_once_with('wx yz')


    @patch('src.log.i')
    def test_should_handle_bad_command(self, mock_i):
        d = src.dispatcher.Dispatcher()

        d.exec_line('bad cmd')

        sert(mock_i).called_once_with('Unrecognized command: bad cmd')



class TestDispatcherReadAndExecLine(unittest.TestCase):

    def test_should_call_exec_line(self):
        d = src.dispatcher.Dispatcher()
        d.read_line = Mock(return_value='some text')
        d.exec_line = Mock()

        d.read_and_exec()

        sert(d.exec_line).called_once_with('some text')


    @patch('__builtin__.raw_input')
    def test_should_call_force_quit(self, mock_input):
        d = src.dispatcher.Dispatcher()
        mock_input.side_effect = EOFError()
        d.force_done = Mock()

        d.read_and_exec()

        sert(d.force_done).called_once()



class TestDispatcherGetConfigVal(unittest.TestCase):

    def test_should_return_value_for_key(self):
        key = 'local-echo'
        d = src.dispatcher.Dispatcher()
        d.config[key].value = True

        ans = d._get_config_val(key)

        sert(ans).is_true()


    def test_should_return_none_for_bad_key(self):
        key = 'bad-key'
        d = src.dispatcher.Dispatcher()

        ans = d._get_config_val(key)

        sert(ans).to_equal(None)



class TestDispatcherIsLocalEcho(unittest.TestCase):

    def test_should_return_value(self):
        key = 'local-echo'
        d = src.dispatcher.Dispatcher()
        d.config[key].value = False

        sert(d.is_local_echo()).is_false()

        d.config[key].value = True

        sert(d.is_local_echo()).is_true()



class TestDispatcherIsExitOnError(unittest.TestCase):

    def test_should_return_value(self):
        key = 'exit-on-error'
        d = src.dispatcher.Dispatcher()
        d.config[key].value = False

        sert(d.is_exit_on_error()).is_false()

        d.config[key].value = True

        sert(d.is_exit_on_error()).is_true()



class TestDispatcherIsTraceOnError(unittest.TestCase):

    def test_should_return_value(self):
        key = 'trace-on-error'
        d = src.dispatcher.Dispatcher()
        d.config[key].value = False

        sert(d.is_trace_on_error()).is_false()

        d.config[key].value = True

        sert(d.is_trace_on_error()).is_true()
