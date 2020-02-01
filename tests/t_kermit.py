import unittest
import datetime
from mock import patch, call, Mock, MagicMock, DEFAULT

import src.log
import src.transport
import src.kermit

from tests.sert import sert, TAttrBag


LEFT_CHEVRON = '\xab'
RIGHT_CHEVRON = '\xbb'



class FakeTransport(src.transport.Transport):

    def __init__(self):
        self.ary = []


    def set_ary(self, rcv=[]):
        self.ary = []
        for r in rcv:
            self.ary.extend([ord(b) for b in r])


    def read_bytes(self, n):
        a = self.ary[:n]
        self.ary = self.ary[n:]
        return a


    def peek(self):
        return self.peek_bytes(1000000000)


    def peek_bytes(self, n):
        return self.ary[:n]


    def clear_buffer(self):
        # Don't really clear the buffer.
        pass


def cmd_str(s):
    return '{} {} {} EVAL'.format(LEFT_CHEVRON, s, RIGHT_CHEVRON)


k = None



class TestParseSendLine(unittest.TestCase):

    @patch('src.kermit.glob')
    def test_should_handle_rename(self, mock_glob):
        mock_glob.glob = Mock(return_value=['a.txt'])

        (is_rename, oldname, newname) = src.kermit.parse_send_line(' a.txt as abc ')

        sert(is_rename).is_true()
        sert(oldname).to_equal('a.txt')
        sert(newname).to_equal('abc')


    def test_should_handle_file_named_as(self):
        (is_rename, oldname, newname) = src.kermit.parse_send_line(' a.txt b.txt as abc ')

        sert(is_rename).is_false()
        sert(oldname).to_equal(None)
        sert(newname).to_equal(None)


    @patch('src.kermit.glob')
    def test_should_handle_wildcard_in_rename(self, mock_glob):
        mock_glob.glob = Mock(return_value=['a2.txt', 'a2.txt'])

        (is_rename, oldname, newname) = src.kermit.parse_send_line(' a* as abc ')

        sert(is_rename).is_true()
        sert(oldname).to_equal(None)
        sert(newname).to_equal(None)



class Base(unittest.TestCase):

    def setUp(self):
        global k

        self.tport = FakeTransport()
        self.tport.write_bytes = MagicMock()

        self.kermit = src.kermit.Kermit(self.tport)
        k = self.kermit



class TestNextCommand(Base):

    def test_should_return_first_command_when_commands_are_populated(self):
        k.takes = ['a', 'b']

        val = k.next_cmd()

        sert(val).to_equal('a')
        sert(k.takes).to_equal(['b'])


    def test_should_return_empty_string_when_no_commands_are_available(self):
        k.takes = []

        val = k.next_cmd()

        sert(val).to_equal('')



class TestFinish(Base):

    def test_should_send_finish_bytes(self):
        sert(self.tport.write_bytes).not_called()

        k.finish()

        sert(self.tport.write_bytes).called_once_with(bytearray(['\x01', '$', ' ', 'G', 'F', '4', '\r']))



class TestHelp(Base):

    @patch('src.log.i')
    def test_should_display_help(self, mock_i):
        k.help('')

        sert(mock_i).any_call('\n  === CONFIG ===')
        sert(mock_i).any_call('\n  === COMMANDS ===')



class TestSend(Base):

    @patch('src.kermit.glob')
    @patch('__builtin__.open')
    def test_should_send_file(self, mock_open, mock_glob):
        rcv_pkts = [
            ['\x01', '+', ' ', 'Y', '~', '&', ' ', '@', '-', '#', ' ', '3', ',', '\r'],
            ['\x01', '&', '!', 'Y', 'A', ',', 'I', ',', '\r'],
            ['\x01', '%', '"', 'Y', '.', '5', '!', '\r'],
            ['\x01', '%', '#', 'Y', '/', 'R', '9', '\r'],
            ['\x01', '%', '$', 'Y', '+', '&', '1', '\r'],
        ]
        snd_pkts = [
            ['\x01', '+', ' ', 'S', '~', '*', ' ', '@', '-', '#', 'N', '3', 'X', '\r'],
            ['\x01', '&', '!', 'F', 'A', '-', 'P', '5', '\r'],
            ['\x01', '2', '"', 'D', '"', 's', 'o', 'm', 'e', ' ', 't', 'e', 'x', 't', '#', 'J', '"', '/', '+', ']', '\r'],
            ['\x01', '%', '#', 'Z', ',', 'X', '"', '\r'],
            ['\x01', '%', '$', 'B', '!', '_', '#', '\r'],
        ]
        self.tport.set_ary(rcv_pkts)
        k.config['transfer'].value = 2 # text
        mock_open.return_value.read.return_value = 'some text\n'
        mock_glob.glob = Mock(return_value=['a.txt'])
        sert(self.tport.write_bytes).not_called()

        k.send(' a.txt ')

        sert(self.tport.write_bytes).called_n_times(5)
        sert(self.tport.write_bytes).nth_call_called_with(1, bytearray(snd_pkts[0]))
        sert(self.tport.write_bytes).nth_call_called_with(2, bytearray(snd_pkts[1]))
        sert(self.tport.write_bytes).nth_call_called_with(3, bytearray(snd_pkts[2]))
        sert(self.tport.write_bytes).nth_call_called_with(4, bytearray(snd_pkts[3]))
        sert(self.tport.write_bytes).nth_call_called_with(5, bytearray(snd_pkts[4]))


    @patch('src.kermit.glob')
    @patch('__builtin__.open')
    @patch('src.log.i')
    def test_should_send_multiple_files(self, mock_i, mock_open, mock_glob):
        snd_pkts = [
            ['\x01', '+', ' ', 'S', '~', '*', ' ', '@', '-', '#', 'N', '3', 'X', '\r'],
            ['\x01', '&', '!', 'F', 'A', '-', 'P', '5', '\r'],
            ['\x01', '2', '"', 'D', '"', 's', 'o', 'm', 'e', ' ', 't', 'e', 'x', 't', '#', 'J', '"', '/', '+', ']', '\r'],
            ['\x01', '%', '#', 'Z', ',', 'X', '"', '\r'],
            ['\x01', '%', '$', 'B', '!', '_', '#', '\r'],
            ['\x01', '+', ' ', 'S', '~', '*', ' ', '@', '-', '#', 'N', '3', 'X', '\r'],
            ['\x01', '&', '!', 'F', 'B', '.', 'Z', '.', '\r'],
            ['\x01', '2', '"', 'D', '"', 'm', 'o', 'r', 'e', ' ', 't', 'e', 'x', 't', '#', 'J', '"', ')', '6', '*', '\r'],
            ['\x01', '%', '#', 'Z', ',', 'X', '"', '\r'],
            ['\x01', '%', '$', 'B', '!', '_', '#', '\r'],
        ]
        rcv_pkts = [
            ['\x01', '+', ' ', 'Y', '~', '&', ' ', '@', '-', '#', ' ', '3', ',', '\r'],
            ['\x01', '(', '!', 'Y', 'A', '.', '1', '"', '8', ';', '\r'],
            ['\x01', '%', '"', 'Y', '.', '5', '!', '\r'],
            ['\x01', '%', '#', 'Y', '/', 'R', '9', '\r'],
            ['\x01', '%', '$', 'Y', '+', '&', '1', '\r'],
            ['\x01', '+', ' ', 'Y', '~', '&', ' ', '@', '-', '#', ' ', '3', ',', '\r'],
            ['\x01', '(', '!', 'Y', 'B', '.', '2', '/', 'O', 'D', '\r'],
            ['\x01', '%', '"', 'Y', '.', '5', '!', '\r'],
            ['\x01', '%', '#', 'Y', '/', 'R', '9', '\r'],
            ['\x01', '%', '$', 'Y', '+', '&', '1', '\r'],
        ]
        self.tport.set_ary(rcv_pkts)
        k.config['transfer'].value = 2 # text
        mock_open.return_value.read.side_effect = ['some text\n', 'more text\n']
        mock_glob.glob = Mock(side_effect=[['a.txt'], ['b.txt']])
        sert(self.tport.write_bytes).not_called()

        k.send(' a.txt b.txt ')

        sert(self.tport.write_bytes).called_n_times(10)
        sert(self.tport.write_bytes).nth_call_called_with( 1, bytearray(snd_pkts[0]))
        sert(self.tport.write_bytes).nth_call_called_with( 2, bytearray(snd_pkts[1]))
        sert(self.tport.write_bytes).nth_call_called_with( 3, bytearray(snd_pkts[2]))
        sert(self.tport.write_bytes).nth_call_called_with( 4, bytearray(snd_pkts[3]))
        sert(self.tport.write_bytes).nth_call_called_with( 5, bytearray(snd_pkts[4]))
        sert(self.tport.write_bytes).nth_call_called_with( 6, bytearray(snd_pkts[5]))
        sert(self.tport.write_bytes).nth_call_called_with( 7, bytearray(snd_pkts[6]))
        sert(self.tport.write_bytes).nth_call_called_with( 8, bytearray(snd_pkts[7]))
        sert(self.tport.write_bytes).nth_call_called_with( 9, bytearray(snd_pkts[8]))
        sert(self.tport.write_bytes).nth_call_called_with(10, bytearray(snd_pkts[9]))

        sert(mock_i).any_call('Sending file 1 of 2')
        sert(mock_i).any_call('Sending file 2 of 2')
        sert(mock_i).any_call('Sending file a.txt as A')
        sert(mock_i).any_call('Sending file b.txt as B')


    @patch('src.kermit.glob')
    @patch('__builtin__.open')
    @patch('src.log.i')
    def test_should_send_renamed_file(self, mock_i, mock_open, mock_glob):
        rcv_pkts = [
            ['\x01', '+', ' ', 'Y', '~', '&', ' ', '@', '-', '#', ' ', '3', ',', '\r'],
            ['\x01', '&', '!', 'Y', 'A', ',', 'I', ',', '\r'],
            ['\x01', '%', '"', 'Y', '.', '5', '!', '\r'],
            ['\x01', '%', '#', 'Y', '/', 'R', '9', '\r'],
            ['\x01', '%', '$', 'Y', '+', '&', '1', '\r'],
        ]
        self.tport.set_ary(rcv_pkts)
        mock_open.return_value.read.return_value = 'some text\n'
        mock_glob.glob = Mock(return_value=['a.txt'])

        k.send(' a.txt as abc ')

        sert(mock_i).any_call('Sending file a.txt as abc')


    @patch('src.kermit.glob')
    @patch('src.log.i')
    def test_should_raise_exception_when_no_file_found(self, mock_i, mock_glob):
        mock_glob.glob = Mock(return_value=[])

        self.assertRaises(Exception, k.send, ' bad-file.txt ')

        sert(mock_i).called_once_with('No files found for bad-file.txt')



class TestGet(Base):

    @patch('__builtin__.open')
    def test_should_get_multiple_files(self, mock_open):
        rcv_pkts = [
            ['\x01', '+', ' ', 'S', '~', '*', ' ', '@', '-', '#', 'Y', '3', '$', '\r'],
            ['\x01', '&', '!', 'F', 'A', '-', 'P', '5', '\r'],
            ['\x01', '@', '"', 'D', 'H', 'P', 'H', 'P', '4', '8', '-', 'P', ',', '*', '#', '\xd0', '#', 'A', '#', '@', 's', 'o', 'm', 'e', ' ', 't', 'e', 'x', 't', '#', 'J', ',', 'T', 'G', '\r'],
            ['\x01', '%', '#', 'Z', ',', 'X', '"', '\r'],
            ['\x01', '%', '$', 'B', '!', '_', '#', '\r'],
            ['\x01', '+', ' ', 'S', '~', '*', ' ', '@', '-', '#', 'Y', '3', '$', '\r'],
            ['\x01', '&', '!', 'F', 'B', '.', 'Z', '.', '\r'],
            ['\x01', '@', '"', 'D', 'H', 'P', 'H', 'P', '4', '8', '-', 'P', ',', '*', '#', '\xd0', '#', 'A', '#', '@', 'm', 'o', 'r', 'e', ' ', 't', 'e', 'x', 't', '#', 'J', ')', 'P', '#', '\r'],
            ['\x01', '%', '#', 'Z', ',', 'X', '"', '\r'],
            ['\x01', '%', '$', 'B', '!', '_', '#', '\r'],
        ]
        snd_pkts = [
            ['\x01', '$', ' ', 'R', 'A', ':', '\r'],
            ['\x01', '+', ' ', 'Y', 'y', '*', ' ', ' ', '-', '#', 'Y', '3', 'D', '\r'],
            ['\x01', '%', '!', 'Y', ',', '\\', 'I', '\r'],
            ['\x01', '%', '"', 'Y', '.', '5', '!', '\r'],
            ['\x01', '%', '#', 'Y', '/', 'R', '9', '\r'],
            ['\x01', '%', '$', 'Y', '+', '&', '1', '\r'],
            ['\x01', '$', ' ', 'R', 'B', ';', '\r'],
            ['\x01', '+', ' ', 'Y', 'y', '*', ' ', ' ', '-', '#', 'Y', '3', 'D', '\r'],
            ['\x01', '%', '!', 'Y', ',', '\\', 'I', '\r'],
            ['\x01', '%', '"', 'Y', '.', '5', '!', '\r'],
            ['\x01', '%', '#', 'Y', '/', 'R', '9', '\r'],
            ['\x01', '%', '$', 'Y', '+', '&', '1', '\r'],
        ]
        self.tport.set_ary(rcv_pkts)

        k.get(' A  B ')

        sert(mock_open).called_twice()
        sert(mock_open).first_call_called_with('A', 'wb')
        sert(mock_open, 'write').first_call_called_with(bytearray(b'HPHP48-P,*\x90\x01\x00some text\n'))
        sert(mock_open).second_call_called_with('B', 'wb')
        sert(mock_open, 'write').second_call_called_with(bytearray(b'HPHP48-P,*\x90\x01\x00more text\n'))
        sert(mock_open, 'close').called_twice()


    @patch('src.log.i')
    def test_should_log_bad_name(self, mock_i):
        k.get('')

        sert(mock_i).called_once_with('Invalid or missing name: ')



class TestReceive(Base):

    def test_should_receive(self):
        k._receive = Mock()

        k.receive()

        sert(k._receive).called_once()



class TestServer(Base):

    @patch('os.getcwd', new=Mock(return_value='/orig/dir'))
    @patch('os.chdir')
    def test_should_launch_server(self, mock_chdir):
        k._server = Mock()

        k.server('./tgt/dir')

        sert(mock_chdir).called_twice()
        sert(mock_chdir).first_call_called_with('./tgt/dir')
        sert(mock_chdir).second_call_called_with('/orig/dir')


    @patch('os.getcwd', new=Mock(return_value='/orig/dir'))
    @patch('os.chdir')
    def test_should_handle_keyboard_interrupt(self, mock_chdir):
        k._server = Mock(side_effect=KeyboardInterrupt)

        k.server('./tgt/dir')

        sert(mock_chdir).called_twice()
        sert(mock_chdir).first_call_called_with('./tgt/dir')
        sert(mock_chdir).second_call_called_with('/orig/dir')


    def test_should_handle_empty_path(self):
        k._server = Mock()

        k.server('')

        sert(k._server).called_once()



class TestRemoteCwd(Base):

    def test_should_default_to_home(self):
        k.send_command = Mock()

        k.remote_cwd('')

        sert(k.send_command).called_with('{ HOME } EVAL')


    def test_should_add_braces(self):
        k.send_command = Mock()

        k.remote_cwd('HOME AAA')

        sert(k.send_command).called_with('{ HOME AAA } EVAL')


    def test_should_eval_dir_with_braces(self):
        k.send_command = Mock()

        k.remote_cwd('{ HOME AAA }')

        sert(k.send_command).called_with('{ HOME AAA } EVAL')



class TestRemoteDelete(Base):

    def test_should_eval_purge(self):
        k.send_command = Mock()

        k.remote_delete(' B ')

        sert(k.send_command).called_with(cmd_str('B PURGE'))



class TestRemoteDirectory(Base):

    def test_should_eval_vars(self):
        k.send_command = Mock()

        k.remote_directory()

        sert(k.send_command).called_with(cmd_str('VARS'))



class TestRemoteHost(Base):

    def test_should_eval(self):
        k.send_command = Mock()

        k.remote_host(' 2 + 3 ')

        sert(k.send_command).called_with('2 + 3')



class TestRemotePath(Base):

    def test_should_eval(self):
        k.send_command = Mock()

        k.remote_path()

        sert(k.send_command).called_with(cmd_str('PATH'))



class TestRemoteSpace(Base):

    def test_should_eval(self):
        k.send_command = Mock()

        k.remote_space()

        sert(k.send_command).called_with(cmd_str('MEM'))



class TestRemoteType(Base):

    def test_should_eval(self):
        k.send_command = Mock()

        k.remote_type(' B ')

        sert(k.send_command).called_with("'B' RCL")



class TestTake(Base):

    @patch('__builtin__.open')
    def test_should_read_file(self, mock_open):
        mock_open.return_value.readlines.return_value = ['line1 cmd\n', 'line2 cmd']
        sert(k.takes).to_equal([])

        k.take(' a.txt ')

        sert(k.takes).to_equal(['line1 cmd', 'line2 cmd'])


    @patch('__builtin__.open')
    def test_should_skip_comment_lines(self, mock_open):
        mock_open.return_value.readlines.return_value = [';comment line1\n', 'line2 cmd']
        sert(k.takes).to_equal([])

        k.take(' a.txt ')

        sert(k.takes).to_equal(['line2 cmd'])


    @patch('__builtin__.open')
    def test_should_skip_empty_lines(self, mock_open):
        mock_open.return_value.readlines.return_value = ['\n', 'line1 cmd\n', '   \n', 'line2 cmd']
        sert(k.takes).to_equal([])

        k.take(' a.txt ')

        sert(k.takes).to_equal(['line1 cmd', 'line2 cmd'])



class TestEcho(Base):

    @patch('src.log.i')
    def test_should_echo(self, mock_i):
        txt = 'some text'

        k.echo(txt)

        sert(mock_i).called_once_with(txt)



class TestLocalCwd(Base):

    @patch('os.chdir')
    def test_should_local_cwd(self, mock_chdir):
        sert(mock_chdir).not_called()

        k.local_cwd('adir')

        sert(mock_chdir).called_once_with('adir')



class TestLocalDelete(Base):

    @patch('os.getcwd', new=Mock(return_value='/a/dir'))
    @patch('glob.glob', new=Mock(return_value=['aglobfile.txt']))
    @patch('os.path.isfile', new=Mock(return_value=True))
    @patch('os.remove')
    def test_should_delete_file(self, mock_remove):
        sert(mock_remove).not_called()

        k.local_delete('afile.txt')

        sert(mock_remove).called_once_with('/a/dir/aglobfile.txt')

    @patch('os.getcwd', new=Mock(return_value='/a/dir'))
    @patch('glob.glob', new=Mock(return_value=['aglobdir']))
    @patch('os.path.isfile', new=Mock(return_value=False))
    @patch('os.path.isdir', new=Mock(return_value=True))
    @patch('os.rmdir')
    def test_should_delete_dir(self, mock_rmdir):
        sert(mock_rmdir).not_called()

        k.local_delete('dirname')

        sert(mock_rmdir).called_once_with('/a/dir/aglobdir')

    @patch('os.getcwd', new=Mock(return_value='/a/dir'))
    @patch('glob.glob', new=Mock(return_value=['aglobfile.txt']))
    @patch('os.path.isfile', new=Mock(return_value=True))
    @patch('os.remove', new=Mock(side_effect=OSError('failed')))
    @patch('src.log.i')
    def test_should_raise_on_delete_file(self, mock_i):
        k.local_delete('afile.txt')

        sert(mock_i).called_once_with('Delete /a/dir/aglobfile.txt failed.')

    @patch('os.getcwd', new=Mock(return_value='/a/dir'))
    @patch('glob.glob', new=Mock(return_value=['aglobdir']))
    @patch('os.path.isfile', new=Mock(return_value=False))
    @patch('os.path.isdir', new=Mock(return_value=True))
    @patch('os.rmdir', new=Mock(side_effect=OSError('failed')))
    @patch('src.log.i')
    def test_should_raise_on_delete_dir(self, mock_i):
        k.local_delete('dirname')

        sert(mock_i).called_once_with('Delete /a/dir/aglobdir failed.')


    @patch('os.getcwd', new=Mock(return_value='/a/dir'))
    @patch('glob.glob', new=Mock(return_value=['aglobdir']))
    @patch('os.path.isfile', new=Mock(return_value=False))
    @patch('os.path.isdir', new=Mock(return_value=False))
    @patch('src.log.i')
    def test_should_raise_on_delete_dir(self, mock_i):
        k.local_delete('not_file_or_dir')

        sert(mock_i).called_once_with('/a/dir/aglobdir is not a file or dir. Ignored.')


def mtime(yr=1970, mon=1, day=1, hr=0, min=0):
    # Compute adjustment to params in order to handle UTC offset and Daylight Saving.
    dtdt = datetime.datetime
    utc_epoch = dtdt.fromtimestamp(0)
    local_epoch = dtdt(*[int(v) for v in utc_epoch.strftime('%Y %m %d %H %M').split()])
    offset = (utc_epoch - local_epoch).total_seconds()
    tm = dtdt(yr, mon, day, hr, min)
    return (tm - utc_epoch).total_seconds() + offset


def call_args_to_ary(call_args):
    ary = []
    for call in call_args:
        tup = call.args
        sert(len(tup)).to_equal(1)
        parts = tup[0].split()
        sert(len(parts)).to_equal(4)
        nam = parts[3]
        is_dir = False
        if nam.startswith('[') and nam.endswith(']'):
            nam = nam[1:-1]
            is_dir = True
        ary.append(TAttrBag(date=parts[0]+'_'+parts[1], size=parts[2], name=nam, isdir=is_dir))
    return ary



class TestLocalDirectory(Base):

    def setUp(self):
        super(TestLocalDirectory, self).setUp()

        self.stat_call_count = 0

        self.fake_files = [
          TAttrBag(name='ac', isdir=False, stat=TAttrBag(st_size=400, st_mtime=mtime(1982, 1, 1))),
          TAttrBag(name='ab', isdir=True, stat=TAttrBag(st_size=400, st_mtime=mtime(1982, 1, 1))),
          TAttrBag(name='aa', isdir=False, stat=TAttrBag(st_size=200, st_mtime=mtime(1986, 1, 1))),
        ]


        patch_getcwd = patch('os.getcwd')
        patch_isdir = patch('os.path.isdir')
        patch_listdir = patch('os.listdir')
        patch_stat = patch('os.stat')
        patch_glob = patch('glob.glob')

        self.addCleanup(patch_getcwd.stop)
        self.addCleanup(patch_isdir.stop)
        self.addCleanup(patch_listdir.stop)
        self.addCleanup(patch_stat.stop)
        self.addCleanup(patch_glob.stop)

        self.mock_getcwd = patch_getcwd.start()
        self.mock_isdir = patch_isdir.start()
        self.mock_listdir = patch_listdir.start()
        self.mock_stat = patch_stat.start()
        self.mock_glob = patch_glob.start()

        # For some reason, tho mocked 'os.stat' is not unpatched after the test
        # completes. This results in the mock being called, rather than the
        # real os.stat() function. callable_stat() works around this issue.
        def callable_stat(fname):
            if self.stat_call_count < len(self.fake_files):
                self.stat_call_count += 1
                return self.fake_files[self.stat_call_count - 1].stat
            return DEFAULT

        self.mock_getcwd.return_value = '/adir'
        self.mock_stat.side_effect = callable_stat # Work-around
        self.mock_listdir.return_value = [f.name for f in self.fake_files]
        self.mock_isdir.side_effect = [False] + [f.isdir for f in self.fake_files]
        self.mock_glob.side_effect = [['aa1'], ['bb1'], ['cc1']]


    @patch('src.log.i')
    def test_should_sort_by_date_size_name_asc(self, mock_i):
        k.config['order-by'].value = 0 # dsn
        k.config['oslope'].value = 1 # asc

        k.local_directory()

        sert(mock_i).called_n_times(3)
        ary = call_args_to_ary(src.log.i.call_args_list)
        prev = ary[0]
        name_checked = False
        for cur in ary[1:]:
            sert(cur.date >= prev.date).is_true()
            if (cur.date == prev.date):
                sert(cur.size >= prev.size).is_true()
                if (cur.size == prev.size):
                    sert(cur.name > prev.name).is_true()
                    name_checked = True
            prev = cur
        sert(name_checked).is_true()


    @patch('src.log.i')
    def test_should_sort_by_date_size_name_desc(self, mock_i):
        k.config['order-by'].value = 0 # dsn
        k.config['oslope'].value = -1 # desc

        k.local_directory()

        sert(mock_i).called_n_times(3)
        ary = call_args_to_ary(src.log.i.call_args_list)
        prev = ary[0]
        name_checked = False
        for cur in ary[1:]:
            sert(cur.date <= prev.date).is_true()
            if (cur.date == prev.date):
                sert(cur.size <= prev.size).is_true()
                if (cur.size == prev.size):
                    sert(cur.name < prev.name).is_true()
                    name_checked = True
            prev = cur
        sert(name_checked).is_true()


    @patch('src.log.i')
    def test_should_sort_by_date_name_asc(self, mock_i):
        k.config['order-by'].value = 2 # dn
        k.config['oslope'].value = 1 # asc

        k.local_directory()

        sert(mock_i).called_n_times(3)
        ary = call_args_to_ary(src.log.i.call_args_list)
        prev = ary[0]
        name_checked = False
        for cur in ary[1:]:
            sert(cur.date >= prev.date).is_true()
            if (cur.date == prev.date):
                sert(cur.name > prev.name).is_true()
                name_checked = True
            prev = cur
        sert(name_checked).is_true()


    @patch('src.log.i')
    def test_should_sort_by_date_name_desc(self, mock_i):
        k.config['order-by'].value = 2 # dn
        k.config['oslope'].value = -1 # desc

        k.local_directory()

        sert(mock_i).called_n_times(3)
        ary = call_args_to_ary(src.log.i.call_args_list)
        prev = ary[0]
        name_checked = False
        for cur in ary[1:]:
            sert(cur.date <= prev.date).is_true()
            if (cur.date == prev.date):
                sert(cur.name < prev.name).is_true()
                name_checked = True
            prev = cur
        sert(name_checked).is_true()


    @patch('src.log.i')
    def test_should_sort_by_size_name_asc(self, mock_i):
        k.config['order-by'].value = 3 # sn
        k.config['oslope'].value = 1 # asc

        k.local_directory()

        sert(mock_i).called_n_times(3)
        ary = call_args_to_ary(src.log.i.call_args_list)
        prev = ary[0]
        name_checked = False
        for cur in ary[1:]:
            sert(cur.size >= prev.size).is_true()
            if (cur.size == prev.size):
                sert(cur.name > prev.name).is_true()
                name_checked = True
            prev = cur
        sert(name_checked).is_true()


    @patch('src.log.i')
    def test_should_sort_by_size_name_desc(self, mock_i):
        k.config['order-by'].value = 3 # sn
        k.config['oslope'].value = -1 # desc

        k.local_directory()

        sert(mock_i).called_n_times(3)
        ary = call_args_to_ary(src.log.i.call_args_list)
        prev = ary[0]
        name_checked = False
        for cur in ary[1:]:
            sert(cur.size <= prev.size).is_true()
            if (cur.size == prev.size):
                sert(cur.name < prev.name).is_true()
                name_checked = True
            prev = cur
        sert(name_checked).is_true()


    @patch('src.log.i')
    def test_should_sort_by_size_date_name_asc(self, mock_i):
        k.config['order-by'].value = 1 # sdn
        k.config['oslope'].value = 1 # asc

        k.local_directory()

        sert(mock_i).called_n_times(3)
        ary = call_args_to_ary(src.log.i.call_args_list)
        prev = ary[0]
        name_checked = False
        for cur in ary[1:]:
            sert(cur.size >= prev.size).is_true()
            if (cur.size == prev.size):
                sert(cur.date >= prev.date).is_true()
                if (cur.date == prev.date):
                    sert(cur.name > prev.name).is_true()
                    name_checked = True
            prev = cur
        sert(name_checked).is_true()


    @patch('src.log.i')
    def test_should_sort_by_size_date_name_desc(self, mock_i):
        k.config['order-by'].value = 1 # sdn
        k.config['oslope'].value = -1 # desc

        k.local_directory()

        sert(mock_i).called_n_times(3)
        ary = call_args_to_ary(src.log.i.call_args_list)
        prev = ary[0]
        name_checked = False
        for cur in ary[1:]:
            sert(cur.size <= prev.size).is_true()
            if (cur.size == prev.size):
                sert(cur.date <= prev.date).is_true()
                if (cur.date == prev.date):
                    sert(cur.name < prev.name).is_true()
                    name_checked = True
            prev = cur
        sert(name_checked).is_true()


    @patch('src.log.i')
    def test_should_sort_by_name_asc(self, mock_i):
        k.config['order-by'].value = 4 # n
        k.config['oslope'].value = 1 # asc

        k.local_directory()

        sert(mock_i).called_n_times(3)
        ary = call_args_to_ary(src.log.i.call_args_list)
        prev = ary[0]
        name_checked = False
        for cur in ary[1:]:
            sert(cur.isdir <= prev.isdir).is_true()
            if (cur.isdir == prev.isdir):
                sert(cur.name > prev.name).is_true()
                name_checked = True
            prev = cur
        sert(name_checked).is_true()


    @patch('src.log.i')
    def test_should_sort_by_name_desc(self, mock_i):
        k.config['order-by'].value = 4 # n
        k.config['oslope'].value = -1 # desc

        k.local_directory()

        sert(mock_i).called_n_times(3)
        ary = call_args_to_ary(src.log.i.call_args_list)
        prev = ary[0]
        name_checked = False
        for cur in ary[1:]:
            sert(cur.isdir >= prev.isdir).is_true()
            if (cur.isdir == prev.isdir):
                sert(cur.name < prev.name).is_true()
                name_checked = True
            prev = cur
        sert(name_checked).is_true()


    @patch('src.log.i')
    def test_should_list_directory(self, mock_i):
        adir = '/a/dir/name'
        self.mock_isdir.side_effect = [True] + [f.isdir for f in self.fake_files]
        k.config['order-by'].value = 4 # n
        k.config['oslope'].value = 1 # asc

        k.local_directory(adir)

        sert(self.mock_listdir).called_once_with(adir)
        sert(mock_i).called_n_times(3)
        ary = call_args_to_ary(src.log.i.call_args_list)
        prev = ary[0]
        name_checked = False
        for cur in ary[1:]:
            sert(cur.isdir <= prev.isdir).is_true()
            if (cur.isdir == prev.isdir):
                sert(cur.name > prev.name).is_true()
                name_checked = True
            prev = cur
        sert(name_checked).is_true()


    @patch('src.log.i')
    def test_should_glob_filespec(self, mock_i):
        filespec = 'aa bb cc'
        k.config['order-by'].value = 4 # n
        k.config['oslope'].value = 1 # asc

        k.local_directory(filespec)

        sert(self.mock_glob).called_n_times(3)
        sert(self.mock_glob).nth_call_called_with(1, 'aa')
        sert(self.mock_glob).nth_call_called_with(2, 'bb')
        sert(self.mock_glob).nth_call_called_with(3, 'cc')
        ary = call_args_to_ary(mock_i.call_args_list)
        prev = ary[0]
        name_checked = False
        for cur in ary[1:]:
            sert(cur.isdir <= prev.isdir).is_true()
            if (cur.isdir == prev.isdir):
                sert(cur.name > prev.name).is_true()
                name_checked = True
            prev = cur
        sert(name_checked).is_true()


    @patch('src.util.key_for_val', new=Mock(return_value='z'))
    @patch('src.log.e')
    def test_should_handle_bad_sort_char(self, mock_e):
        k.local_directory()

        sert(mock_e).called_once_with('Bad field char {}'.format('z'))



class TestLocalPath(Base):

    @patch('os.getcwd')
    @patch('src.log.i')
    def test_should_delete_file(self, mock_i, mock_getcwd):
        mock_getcwd.return_value = 'curdir'

        k.local_path()

        sert(mock_i).called_once_with('curdir')



class TestLocalPush(Base):

    @patch('os.system')
    @patch('os.name', new_callable=Mock(return_value='posix'))
    def test_should_call_bash(self, mock_name, mock_system):
        sert(mock_system).not_called()

        k.local_push()

        sert(mock_system).called_once_with('bash')


    @patch('os.system')
    @patch('os.name', new_callable=Mock(return_value='nt'))
    def test_should_call_commandcom(self, mock_name, mock_system):
        sert(mock_system).not_called()

        k.local_push()

        sert(mock_system).called_once_with('command.com')


    @patch('os.system')
    def test_should_call_config_shell(self, mock_system):
        k.config['shell'].value = 'ashell'
        sert(mock_system).not_called()

        k.local_push()

        sert(mock_system).called_once_with('ashell')


    @patch('os.name', new_callable=Mock(return_value='unknown_name'))
    @patch('src.log.e')
    def test_should_call_c(self, mock_e, mock_name):
        k.config['shell'].value = None

        k.local_push()

        sert(mock_e).called_once_with("Unknown shell. (Set the 'shell' config value)")



class TestLocalRun(Base):

    @patch('os.system')
    def test_should_push(self, mock_system):
        sert(mock_system).not_called()

        k.local_run('acmd')

        sert(mock_system).called_once_with('acmd')



class TestLocalSpace(Base):

    @patch('os.getcwd', new=Mock(return_value='/a/dir'))
    @patch('os.statvfs', new=Mock(return_value=TAttrBag(f_blocks=10000, f_bavail=200, f_frsize=1000)))
    @patch('src.log.i')
    def test_should_space(self, mock_i):
        k.local_space()

        sert(mock_i).called_n_times(3)



class TestLocalType(Base):

    @patch('__builtin__.open')
    @patch('src.log.i')
    def test_should_type(self, mock_i, mock_open):
        mock_open.return_value.read.return_value = ['some text\n', 'more text']

        k.local_type(' a.txt ')

        sert(mock_i).called_once_with(['some text\n', 'more text'])


    @patch('src.log.e')
    def test_should_handle_missing_filename(self, mock_e):

        k.local_type('')

        sert(mock_e).called_once_with('Missing filename')



class TestShow(Base):

    @patch('src.log.i')
    def test_should_show_config(self, mock_i):
        k.show('')

        # Spot-check a few items
        sert(mock_i).any_call('  default-name: KDAT')
        sert(mock_i).any_call('      timeout        : 10')
        sert(len(mock_i.call_args_list)).to_equal(30)



class TestSet(Base):

    @patch('src.kermit.util.set_config')
    def test_should_ignore_bad_name(self, mock_set_config):

        k.set('bad-name 5')

        sert(mock_set_config).not_called()


    def test_should_set_chr(self):
        sert(k.config['comment-char'].validator).to_equal(chr)
        sert(k.config['comment-char'].value).to_equal(';')

        k.set('comment-char #')

        sert(k.config['comment-char'].value).to_equal('#')


    def test_should_set_int(self):
        sert(k.config['send']['packet-length'].validator).to_equal(int)
        sert(k.config['send']['packet-length'].value).to_equal(94)

        k.set('send packet-length 40')

        sert(k.config['send']['packet-length'].value).to_equal(40)


    def test_should_set_str(self):
        sert(k.config['default-name'].validator).to_equal(str)
        sert(k.config['default-name'].value).to_equal('KDAT')

        k.set('default-name ABC')

        sert(k.config['default-name'].value).to_equal('ABC')


    def test_should_set_subkey(self):
        sert(k.config['send']['ctl-prefix'].value).to_equal('#')

        k.set('send ctl-prefix $')

        sert(k.config['send']['ctl-prefix'].value).to_equal('$')


    def test_should_set_debug_off(self):
        k.config['debug'].value = 1
        sert(k.config['debug'].value).to_equal(1)

        k.set('debug off')

        sert(k.config['debug'].value).to_equal(0)


    def test_should_set_debug_on(self):
        k.config['debug'].value = 0
        sert(k.config['debug'].value).to_equal(0)

        k.set('debug on')

        sert(k.config['debug'].value).to_equal(1)


    def test_should_set_blockcheck_1(self):
        sert(k.config['send']['block-check'].value).to_equal(3)

        k.set('send block-check 1')

        sert(k.config['send']['block-check'].value).to_equal(1)


    def test_should_set_blockcheck_2(self):
        sert(k.config['send']['block-check'].value).to_equal(3)

        k.set('send block-check 2')

        sert(k.config['send']['block-check'].value).to_equal(2)


    def test_should_set_blockcheck_3(self):
        k.config['send']['block-check'].value = 1
        sert(k.config['send']['block-check'].value).to_equal(1)

        k.set('send block-check 3')

        sert(k.config['send']['block-check'].value).to_equal(3)


    def test_should_set_transfer_binary(self):
        k.config['transfer'].value = 2
        sert(k.config['transfer'].value).to_equal(2)

        k.set('transfer binary')

        sert(k.config['transfer'].value).to_equal(1)


    def test_should_set_transfer_text(self):
        k.config['transfer'].value = 1
        sert(k.config['transfer'].value).to_equal(1)

        k.set('transfer text')

        sert(k.config['transfer'].value).to_equal(2)


    def test_should_set_warning_off(self):
        sert(k.config['warning'].value).to_equal(1)

        k.set('warning off')

        sert(k.config['warning'].value).to_equal(0)


    def test_should_set_warning_on(self):
        k.config['warning'].value = 0
        sert(k.config['warning'].value).to_equal(0)

        k.set('warning on')

        sert(k.config['warning'].value).to_equal(1)


    @patch('src.log.i')
    def test_should_skip_set_receive(self, mock_i):
        sert(k.config['receive']['timeout'].value).to_equal(10)

        k.set('receive timeout 2')

        sert(mock_i).called_once_with('Cannot set receive')
        sert(k.config['receive']['timeout'].value).to_equal(10)
