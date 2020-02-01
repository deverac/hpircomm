import unittest
from mock import patch, call, Mock, MagicMock, DEFAULT

import src.kprotocol

from tests.sert import sert, TAttrBag


def unch(ch):
    return ord(ch) - 32



class TestCtl(unittest.TestCase):

    def test_should_clear_bit(self):
        sert(src.kprotocol.ctl(0xff)).to_equal(0xBF)


    def test_should_set_bit(self):
        sert(src.kprotocol.ctl(0xBF)).to_equal(0xFF)



class TestToChar(unittest.TestCase):

    def test_should_convert_int_to_char(self):
        sert(src.kprotocol.toChar(65)).to_equal('a')
        sert(src.kprotocol.toChar(94)).to_equal('~')



class TestUnChar(unittest.TestCase):

    def test_should_convert_char_to_int(self):
        sert(src.kprotocol.unChar('a')).to_equal(65)
        sert(src.kprotocol.unChar('~')).to_equal(94)



class TestP(unittest.TestCase):

    def test_should_incr_and_wrap_seq(self):
        p = src.kprotocol.P()
        for i in range(0, 3*64):
            sert(p._seq()).to_equal(i % 64)


    def test_should_set_default_blockcheck(self):
        sert(src.kprotocol.P().blockcheck).to_equal(1)


    def test_should_set_supplied_blockcheck(self):
        sert(src.kprotocol.P(1).blockcheck).to_equal(1)
        sert(src.kprotocol.P(2).blockcheck).to_equal(2)
        sert(src.kprotocol.P(3).blockcheck).to_equal(3)
        sert(src.kprotocol.P(243).blockcheck).to_equal(243)


    def test_should_create_packet_types(self):
        p = src.kprotocol.P()
        sert(p.send_initiate().type).to_equal('S')
        sert(p.receive_initiate('a').type).to_equal('R')
        sert(p.initialize().type).to_equal('I')
        sert(p.file_header('a').type).to_equal('F')
        sert(p.text_header().type).to_equal('X')
        sert(p.error('a').type).to_equal('E')
        sert(p.data('a').type).to_equal('D')
        sert(p.remote_host('a').type).to_equal('C')
        sert(p.end_of_file().type).to_equal('Z')
        sert(p.end_of_trans().type).to_equal('B')
        sert(p.finish().type).to_equal('G')


    def test_should_create_ack_packet(self):
        pkt = src.kprotocol.P().finish()
        ack_pkt = src.kprotocol.P().ack(pkt)

        sert(ack_pkt.type).to_equal('Y')
        sert(ack_pkt.seq_ch).to_equal(pkt.seq_ch)


    def test_should_create_nack_packet(self):
        pkt = src.kprotocol.P().finish()
        nack_pkt = src.kprotocol.P().nack(pkt)

        sert(nack_pkt.type).to_equal('N')
        sert(nack_pkt.seq_ch).to_equal(pkt.seq_ch)


    def test_should_compute_checksum_with_payload(self):
        sert(src.kprotocol.P().data('some data'   ).checksum()).to_equal('!')
        sert(src.kprotocol.P().data('some data', 1).checksum()).to_equal('!')
        sert(src.kprotocol.P().data('some data', 2).checksum()).to_equal(['/', '_'])
        sert(src.kprotocol.P().data('some data', 3).checksum()).to_equal(['%', '=', '9'])


    def test_should_compute_checksum_without_payload(self):
        sert(src.kprotocol.P().text_header( ).checksum()).to_equal('=')
        sert(src.kprotocol.P().text_header(1).checksum()).to_equal('=')
        sert(src.kprotocol.P().text_header(2).checksum()).to_equal(['"', '<'])
        sert(src.kprotocol.P().text_header(3).checksum()).to_equal([',', '=', 'X'])


    def test_should_handle_checksum_exception(self):
        pkt = src.kprotocol.P().data('some data')
        pkt.blockcheck = 4

        with self.assertRaises(Exception) as cm:
            pkt.checksum()

        sert(cm.exception.message).to_equal('Invalid checksum blockcheck 4')


    def test_should_compute_length_with_payload(self):
        sert(src.kprotocol.P().data('some data'   ).length()).to_equal(',')
        sert(src.kprotocol.P().data('some data', 1).length()).to_equal(',')
        sert(src.kprotocol.P().data('some data', 2).length()).to_equal('-')
        sert(src.kprotocol.P().data('some data', 3).length()).to_equal('.')


    def test_should_compute_length_without_payload(self):
        sert(src.kprotocol.P().text_header( ).length()).to_equal('#')
        sert(src.kprotocol.P().text_header(1).length()).to_equal('#')
        sert(src.kprotocol.P().text_header(2).length()).to_equal('$')
        sert(src.kprotocol.P().text_header(3).length()).to_equal('%')


    def test_should_handle_length_exception(self):
        pkt = src.kprotocol.P().data('some data')
        pkt.blockcheck = 4

        with self.assertRaises(Exception) as cm:
            pkt.length()

        sert(cm.exception.message).to_equal('Invalid length blockcheck 4')


    def test_should_show_null_string(self):
        pkt = src.kprotocol.P().data('some data')
        pkt.type = None
        sert(str(pkt)).to_equal('(nullPacket)')


    def test_should_show_string(self):
        sert(str(src.kprotocol.P().data('abc'))).to_equal('\x01 &   D a b c R \r')



class TestKermitProtocolGetInitParams(unittest.TestCase):

    def test_should_get_default_init_params(self):
        sert(src.kprotocol.KermitProtocol(Mock()).get_init_params()).to_equal('~* @-#N3')


    def test_should_get_init_params_from_config(self):
        k = src.kprotocol.KermitProtocol(Mock())
        snd = k.config['send']
        snd['packet-length'].value = unch('M')
        snd['timeout'].value = unch('c')
        snd['padding'].value = unch('z')
        snd['padchar'].value = '&'
        snd['end-of-line'].value = unch('a')
        snd['ctl-prefix'].value = '*'
        snd['bin-prefix'].value = 'Z'
        snd['block-check'].value = 4

        sert(k.get_init_params()).to_equal('Mcz&a*Z4')



class TestKermitProtocolSetReceiveParams(unittest.TestCase):

    def test_should(self):
        pkt = src.kprotocol.P().initialize('~* @-#N3')
        mock_transport = Mock()
        k = src.kprotocol.KermitProtocol(mock_transport)

        k.set_receive_params(pkt)

        rcv = k.config['receive']
        sert(rcv['packet-length'].value).to_equal(unch('~'))
        sert(rcv['timeout'].value).to_equal(unch('*'))
        sert(rcv['padding'].value).to_equal(unch(' '))
        sert(rcv['padchar'].value).to_equal('@')
        sert(rcv['end-of-line'].value).to_equal(unch('-'))
        sert(rcv['ctl-prefix'].value).to_equal('#')
        sert(rcv['bin-prefix'].value).to_equal('N')
        sert(rcv['block-check'].value).to_equal(3)



class TestKermitProtocolGetHpName(unittest.TestCase):

    def test_should_return_default_name(self):
        k = src.kprotocol.KermitProtocol(Mock())
        sert(k.get_hp_name(None, None, Mock())).to_equal('KDAT')


    def test_should_return_config_name(self):
        k = src.kprotocol.KermitProtocol(Mock())
        k.config['default-name'].value = 'ZaZ'
        sert(k.get_hp_name('pict.txt', None, Mock())).to_equal('ZaZ')
        sert(k.get_hp_name(None, 'PICT', Mock())).to_equal('ZaZ')


    def test_should_capitalize_basename(self):
        k = src.kprotocol.KermitProtocol(Mock())
        sert(k.get_hp_name('abc.def.txt', None, Mock())).to_equal('ABC')
        sert(k.get_hp_name('abc.txt', None, Mock())).to_equal('ABC')
        sert(k.get_hp_name('efg.', None, Mock())).to_equal('EFG')
        sert(k.get_hp_name('fgh', None, Mock())).to_equal('FGH')
        sert(k.get_hp_name('jk lm.txt', None, Mock())).to_equal('JKLM')


    def test_should_return_name_as_is(self):
        k = src.kprotocol.KermitProtocol(Mock())
        sert(k.get_hp_name(None, 'ab', Mock())).to_equal('ab')
        sert(k.get_hp_name(None, 'Ab', Mock())).to_equal('Ab')
        sert(k.get_hp_name(None, 'Ab-cD', Mock())).to_equal('AbcD')


    def test_should_select_name_over_filename(self):
        k = src.kprotocol.KermitProtocol(Mock())
        sert(k.get_hp_name('cde.txt', 'ab', Mock())).to_equal('ab')



class TestKermitProtocolWritePacket(unittest.TestCase):

    def test_should_write_packet(self):
        mock_transport = Mock()
        k = src.kprotocol.KermitProtocol(mock_transport)
        pkt = src.kprotocol.P().text_header()

        ans = k.write_packet(pkt)

        sert(ans).is_true()
        sert(mock_transport.write_bytes).called_once_with(bytearray(b'\x01# X=\r'))


    @patch('src.kprotocol.log')
    def test_should_handle_no_packet(self, mock_log):
        k = src.kprotocol.KermitProtocol(Mock())

        ans = k.write_packet(None)

        sert(ans).is_false()
        sert(mock_log.e).called_once_with('No packet to write')


    @patch('src.kprotocol.log')
    def test_should_log(self, mock_log):
        k = src.kprotocol.KermitProtocol(Mock())
        k.config['debug'].value = True
        pkt = src.kprotocol.P().text_header()

        ans = k.write_packet(pkt)

        sert(mock_log.i).called_once_with("Sending ['\\x01', '#', ' ', 'X', '=', '\\r']")



class TestKermitProtocolPrepBuffer(unittest.TestCase):

    def test_should_handle_empty_peek(self):
        mock_transport = Mock()
        mock_transport.peek_byte = Mock(return_value=[])
        k = src.kprotocol.KermitProtocol(mock_transport)

        k._prep_buffer()

        sert(mock_transport.read_byte).not_called()


    def test_should_read_until_empty_peek(self):
        mock_transport = Mock()
        mock_transport.peek_byte = Mock(side_effect=[[44], [45], []])
        k = src.kprotocol.KermitProtocol(mock_transport)

        k._prep_buffer()

        sert(mock_transport.read_byte).called_n_times(2)


    def test_should_read_until_default_sop(self):
        sop = 1
        mock_transport = Mock()
        mock_transport.peek_byte = Mock(side_effect=[[43], [44], [45], [sop], [46]])
        k = src.kprotocol.KermitProtocol(mock_transport)

        k._prep_buffer()

        sert(mock_transport.read_byte).called_n_times(3)


    def test_should_read_until_configured_sop(self):
        sop = 9
        mock_transport = MagicMock()
        mock_transport.peek_byte = Mock(side_effect=[[42], [43], [44], [45], [sop], [46]])
        k = src.kprotocol.KermitProtocol(mock_transport)
        k.config['receive']['start-of-packet'].value = sop

        k._prep_buffer()

        sert(mock_transport.read_byte).called_n_times(4)



class TestKermitProtocolRemoteEval(unittest.TestCase):

    def test_should_remote_eval(self):
        k = src.kprotocol.KermitProtocol(Mock())
        k.send_command = Mock()

        k._remote_eval('a b c')

        sert(k.send_command).called_once_with('\xab a b c \xbb EVAL')



class TestKermitProtocolReadyBytes(unittest.TestCase):

    def test_should_return_zero_when_min_length_subceeded(self):
        minlen = 6
        mock_transport = Mock()
        k = src.kprotocol.KermitProtocol(mock_transport)
        mock_transport.peek.return_value = range(1, minlen)

        sert(k._ready_bytes()).to_equal(0)


    def test_should_return_zero_when_packet_is_incomplete(self):
        pkt = '\x01$ XX1\r'
        buf = [ord(x) for x in pkt[0:6]]
        mock_transport = Mock()
        k = src.kprotocol.KermitProtocol(mock_transport)
        mock_transport.peek.return_value = buf

        sert(k._ready_bytes()).to_equal(0)


    def test_should_return_length_when_packet_is_complete(self):
        pkt = '\x01# N3\r'
        buf = [ord(x) for x in pkt]
        mock_transport = Mock()
        k = src.kprotocol.KermitProtocol(mock_transport)
        mock_transport.peek.return_value = buf

        sert(k._ready_bytes()).to_equal(len(buf))



class TestKermitProtocolPollForPacketfulOfBytes(unittest.TestCase):

    @patch('time.sleep')
    def test_should_return_none(self, mock_sleep):
        k = src.kprotocol.KermitProtocol(Mock())
        k._prep_buffer = Mock()
        k._ready_bytes = Mock(return_value=0)

        ans = k._poll_for_packetful_of_bytes()

        sert(ans).to_equal(None)


    @patch('time.sleep')
    def test_should_return_bytes(self, mock_sleep):
        bytes = [65, 66]
        mock_transport = Mock()
        mock_transport.read_bytes = Mock(return_value=bytes)
        k = src.kprotocol.KermitProtocol(mock_transport)
        k._prep_buffer = Mock()
        k._ready_bytes = Mock(return_value=len(bytes))

        ans = k._poll_for_packetful_of_bytes()

        sert(ans).to_equal(bytes)


    @patch('time.sleep')
    def test_should_dislodge_data(self, mock_sleep):
        k = src.kprotocol.KermitProtocol(Mock())
        k._prep_buffer = Mock()
        k._ready_bytes = Mock(return_value=0)
        k._dislodge_stale_data = Mock()

        ans = k._poll_for_packetful_of_bytes()

        sert(k._dislodge_stale_data).called_n_times(58)


    @patch('src.kprotocol.log')
    @patch('time.sleep')
    def test_should_log(self, mock_sleep, mock_log):
        bytes = [65]
        mock_transport = Mock()
        mock_transport.read_bytes = Mock(return_value=bytes)
        k = src.kprotocol.KermitProtocol(mock_transport)
        k.config['debug'].value = True
        k._prep_buffer = Mock()
        k._ready_bytes = Mock(return_value=len(bytes))

        ans = k._poll_for_packetful_of_bytes()

        sert(mock_log.i).called_once_with("Received ['A']")


    @patch('time.sleep')
    def test_should_poll(self, mock_sleep):
        k = src.kprotocol.KermitProtocol(Mock())
        k._prep_buffer = Mock()
        k._ready_bytes = Mock(return_value=0)

        ans = k._poll_for_packetful_of_bytes()

        sert(k._ready_bytes).called_n_times(60)


    @patch('time.sleep')
    def test_should_sleep(self, mock_sleep):
        k = src.kprotocol.KermitProtocol(Mock())
        k._prep_buffer = Mock()
        k._ready_bytes = Mock(return_value=0)
        num = 20

        ans = k._poll_for_packetful_of_bytes(num)

        sert(mock_sleep).called_n_times(num)
        for i in range(1, num+1):
            sert(mock_sleep).nth_call_called_with(i, 0.1)


    @patch('time.sleep')
    def test_should_poll_num_times(self, mock_sleep):
        k = src.kprotocol.KermitProtocol(Mock())
        k._prep_buffer = Mock()
        k._ready_bytes = Mock(return_value=0)
        num = 20

        ans = k._poll_for_packetful_of_bytes(num)

        sert(k._ready_bytes).called_n_times(num)


    @patch('time.sleep')
    def test_should_sleep_with_given_delay(self, mock_sleep):
        k = src.kprotocol.KermitProtocol(Mock())
        k._prep_buffer = Mock()
        k._ready_bytes = Mock(return_value=0)
        num = 20
        delay = 0.3

        ans = k._poll_for_packetful_of_bytes(num, delay)

        sert(mock_sleep).called_n_times(num)
        for i in range(1, num+1):
            sert(mock_sleep).nth_call_called_with(i, delay)



class TestKermitProtocolDislodgeStaleData(unittest.TestCase):

    def test_should_return_none(self):
        bytes = [65, 66]
        mock_transport = Mock()
        mock_transport.peek = Mock(return_value=bytes)
        k = src.kprotocol.KermitProtocol(mock_transport)

        sert(k._dislodge_stale_data(bytes)).to_equal(None)
        sert(mock_transport.read_byte).called_once()


    def test_should_return_peek_bytes(self):
        bytes = [65, 66]
        mock_transport = Mock()
        mock_transport.peek = Mock(return_value=bytes)
        k = src.kprotocol.KermitProtocol(mock_transport)

        sert(k._dislodge_stale_data(None)).to_equal(bytes)
        sert(k._dislodge_stale_data([65])).to_equal(bytes)



class TestKermitProtocolChoose(unittest.TestCase):

    def setUp(self):
        self.p1 = paket('_')
        self.p2 = paket('_')
        self.p3 = paket('_')

    def test_should_choose(self):
        k = src.kprotocol.KermitProtocol(Mock())

        sert(k._choose(None, None, None)).to_equal(None)
        sert(k._choose(self.p1, None,    None   ) == self.p1).is_true()
        sert(k._choose(None,    self.p2, None   ) == self.p2).is_true()
        sert(k._choose(None,    None,    self.p3) == self.p3).is_true()


    def test_should_choose_param1_when_type_is_i(self):
        i1 = paket('I')
        i2 = paket('I')
        i3 = paket('I')
        k = src.kprotocol.KermitProtocol(Mock())

        sert(k._choose(i1, i2, i3) == i1).is_true()


    def test_should_choose_config_param1(self):
        k = src.kprotocol.KermitProtocol(Mock())
        k.config['receive']['block-check'].value = 1

        sert(k._choose(self.p1, self.p2, self.p3) == self.p1).is_true()


    def test_should_choose_config_param2(self):
        k = src.kprotocol.KermitProtocol(Mock())
        k.config['receive']['block-check'].value = 2

        sert(k._choose(self.p1, self.p2, self.p3) == self.p2).is_true()


    def test_should_choose_config_param3(self):
        k = src.kprotocol.KermitProtocol(Mock())
        k.config['receive']['block-check'].value = 3

        sert(k._choose(self.p1, self.p2, self.p3) == self.p3).is_true()


    def test_should_choose_param3_over_param2(self):
        k = src.kprotocol.KermitProtocol(Mock())
        k.config['receive']['block-check'].value = 1

        sert(k._choose(None, self.p2, self.p3) == self.p3).is_true()


    def test_should_choose_param2_over_param1(self):
        k = src.kprotocol.KermitProtocol(Mock())
        k.config['receive']['block-check'].value = 3

        sert(k._choose(self.p1, self.p2, None) == self.p2).is_true()



class TestKermitProtocolReadAnyPacket(unittest.TestCase):

    @patch('time.sleep', new=Mock())
    def test_should_return_none(self):
        k = src.kprotocol.KermitProtocol(Mock())
        k._poll_for_packetful_of_bytes = Mock(return_value=None)

        sert(k.read_any_packet()).to_equal(None)


    def test_should_return_none_for_invalid_bytes(self):
        k = src.kprotocol.KermitProtocol(Mock())
        k._poll_for_packetful_of_bytes = Mock(return_value=[1, 65, 66])

        sert(k.read_any_packet()).to_equal(None)


    def test_should_return_blockcheck1(self):
        blockcheck = 1
        bytes = [ord(b) for b in src.kprotocol.P(blockcheck).finish().to_list()]
        k = src.kprotocol.KermitProtocol(Mock())
        k._poll_for_packetful_of_bytes = Mock(return_value=bytes)

        pkt = k.read_any_packet()

        sert(pkt.to_list()).to_equal(['\x01', '$', ' ', 'G', 'F', '4', '\r'])


    def test_should_return_blockcheck2(self):
        blockcheck = 2
        bytes = [ord(b) for b in src.kprotocol.P(blockcheck).finish().to_list()]
        k = src.kprotocol.KermitProtocol(Mock())
        k._poll_for_packetful_of_bytes = Mock(return_value=bytes)

        pkt = k.read_any_packet()

        sert(pkt.to_list()).to_equal(['\x01', '%', ' ', 'G', 'F', '#', '2', '\r'])


    def test_should_return_blockcheck3(self):
        blockcheck = 3
        bytes = [ord(b) for b in src.kprotocol.P(blockcheck).finish().to_list()]
        k = src.kprotocol.KermitProtocol(Mock())
        k._poll_for_packetful_of_bytes = Mock(return_value=bytes)

        pkt = k.read_any_packet()

        sert(pkt.to_list()).to_equal(['\x01', '&', ' ', 'G', 'F', '.', 'N', 'N', '\r'])



class TestKermitProtocolToPacket(unittest.TestCase):

    def setUp(self):
        self.p1 = ['\x01', '$', ' ', 'D', 'a', 'L', '\r']
        self.p2 = ['\x01', '%', ' ', 'D', 'a', '#', 'J', '\r']
        self.p3 = ['\x01', '&', ' ', 'D', 'a', ')', '1', '[', '\r']

        self.buf1 = [ord(c) for c in self.p1]
        self.buf2 = [ord(c) for c in self.p2]
        self.buf3 = [ord(c) for c in self.p3]


    def test_should_return_none_for_empty_buf(self):
        k = src.kprotocol.KermitProtocol(Mock())
        sert(k.to_packet([], 1)).to_equal(None)


    def test_should_return_none_for_bad_blockcheck(self):
        k = src.kprotocol.KermitProtocol(Mock())
        sert(k.to_packet([65], 0)).to_equal(None)
        sert(k.to_packet([65], 4)).to_equal(None)


    def test_should_return_none_for_min_length(self):
        k = src.kprotocol.KermitProtocol(Mock())
        sert(k.to_packet([65] * 5, 1)).to_equal(None)
        sert(k.to_packet([65] * 6, 2)).to_equal(None)
        sert(k.to_packet([65] * 7, 3)).to_equal(None)


    @patch('src.kprotocol.log')
    def test_should_return_none_for_bad_header1(self, mock_log):
        buf = self.buf1
        buf[0] = 2
        k = src.kprotocol.KermitProtocol(Mock())
        sert(k.to_packet(buf, 1)).to_equal(None)
        sert(mock_log.d).called_once_with('Bad header. Expected:1  Actual:2')


    @patch('src.kprotocol.log')
    def test_should_return_none_for_bad_header2(self, mock_log):
        buf = self.buf2
        buf[0] = 3
        k = src.kprotocol.KermitProtocol(Mock())
        sert(k.to_packet(buf, 2)).to_equal(None)
        sert(mock_log.d).called_once_with('Bad header. Expected:1  Actual:3')


    @patch('src.kprotocol.log')
    def test_should_return_none_for_bad_header3(self, mock_log):
        buf = self.buf3
        buf[0] = 4
        k = src.kprotocol.KermitProtocol(Mock())
        sert(k.to_packet(buf, 3)).to_equal(None)
        sert(mock_log.d).called_once_with('Bad header. Expected:1  Actual:4')


    @patch('src.kprotocol.log')
    def test_should_return_none_for_bad_header1a(self, mock_log):
        buf = self.buf1
        k = src.kprotocol.KermitProtocol(Mock())
        k.config['receive']['start-of-packet'].value = 2
        sert(k.to_packet(buf, 1)).to_equal(None)
        sert(mock_log.d).called_once_with('Bad header. Expected:2  Actual:1')


    @patch('src.kprotocol.log')
    def test_should_return_none_for_bad_header2a(self, mock_log):
        buf = self.buf2
        k = src.kprotocol.KermitProtocol(Mock())
        k.config['receive']['start-of-packet'].value = 3
        sert(k.to_packet(buf, 2)).to_equal(None)
        sert(mock_log.d).called_once_with('Bad header. Expected:3  Actual:1')


    @patch('src.kprotocol.log')
    def test_should_return_none_for_bad_header3a(self, mock_log):
        buf = self.buf3
        k = src.kprotocol.KermitProtocol(Mock())
        k.config['receive']['start-of-packet'].value = 4
        sert(k.to_packet(buf, 3)).to_equal(None)
        sert(mock_log.d).called_once_with('Bad header. Expected:4  Actual:1')


    @patch('src.kprotocol.log')
    def test_should_return_none_for_bad_seq1(self, mock_log):
        buf = self.buf1
        buf[2] = 64 + 32
        k = src.kprotocol.KermitProtocol(Mock())
        sert(k.to_packet(buf, 1)).to_equal(None)
        sert(mock_log.d).called_once_with('Bad seq num. Actual:64 (exceeds 63)')


    @patch('src.kprotocol.log')
    def test_should_return_none_for_bad_seq2(self, mock_log):
        buf = self.buf2
        buf[2] = 64 + 33
        k = src.kprotocol.KermitProtocol(Mock())
        sert(k.to_packet(buf, 2)).to_equal(None)
        sert(mock_log.d).called_once_with('Bad seq num. Actual:65 (exceeds 63)')


    @patch('src.kprotocol.log')
    def test_should_return_none_for_bad_seq3(self, mock_log):
        buf = self.buf3
        buf[2] = 64 + 34
        k = src.kprotocol.KermitProtocol(Mock())
        sert(k.to_packet(buf, 3)).to_equal(None)
        sert(mock_log.d).called_once_with('Bad seq num. Actual:66 (exceeds 63)')


    @patch('src.kprotocol.log')
    def test_should_return_none_for_bad_type1(self, mock_log):
        buf = self.buf1
        buf[3] = ord('a')
        k = src.kprotocol.KermitProtocol(Mock())
        sert(k.to_packet(buf, 1)).to_equal(None)
        sert(mock_log.d).called_once_with('Unknown type:a')


    @patch('src.kprotocol.log')
    def test_should_return_none_for_bad_type2(self, mock_log):
        buf = self.buf2
        buf[3] = ord('b')
        k = src.kprotocol.KermitProtocol(Mock())
        sert(k.to_packet(buf, 2)).to_equal(None)
        sert(mock_log.d).called_once_with('Unknown type:b')


    @patch('src.kprotocol.log')
    def test_should_return_none_for_bad_type3(self, mock_log):
        buf = self.buf3
        buf[3] = ord('c')
        k = src.kprotocol.KermitProtocol(Mock())
        sert(k.to_packet(buf, 3)).to_equal(None)
        sert(mock_log.d).called_once_with('Unknown type:c')


    @patch('src.kprotocol.log')
    def test_should_return_none_for_bad_trailer1(self, mock_log):
        buf = self.buf1
        buf[-1] = 65
        k = src.kprotocol.KermitProtocol(Mock())
        sert(k.to_packet(buf, 1)).to_equal(None)
        sert(mock_log.d).called_once_with('Bad end-of-line. Expected:13  Actual:{}'.format(65))


    @patch('src.kprotocol.log')
    def test_should_return_none_for_bad_trailer2(self, mock_log):
        buf = self.buf2
        buf[-1] = 66
        k = src.kprotocol.KermitProtocol(Mock())
        sert(k.to_packet(buf, 2)).to_equal(None)
        sert(mock_log.d).called_once_with('Bad end-of-line. Expected:13  Actual:66')


    @patch('src.kprotocol.log')
    def test_should_return_none_for_bad_trailer3(self, mock_log):
        buf = self.buf3
        buf[-1] = 67
        k = src.kprotocol.KermitProtocol(Mock())
        sert(k.to_packet(buf, 3)).to_equal(None)
        sert(mock_log.d).called_once_with('Bad end-of-line. Expected:13  Actual:67')


    @patch('src.kprotocol.KermitPacket')
    @patch('src.kprotocol.log')
    def test_should_return_none_for_bad_length1(self, mock_log, mock_kp):
        buf = self.buf1
        k = src.kprotocol.KermitProtocol(Mock())
        mock_kp.return_value.length.return_value = 'a'

        sert(k.to_packet(buf, 1)).to_equal(None)
        sert(mock_log.d).called_once_with('Bad length. Expected:$ Actual:a')


    @patch('src.kprotocol.KermitPacket')
    @patch('src.kprotocol.log')
    def test_should_return_none_for_bad_length2(self, mock_log, mock_kp):
        buf = self.buf2
        k = src.kprotocol.KermitProtocol(Mock())
        mock_kp.return_value.length.return_value = 'b'

        sert(k.to_packet(buf, 2)).to_equal(None)
        sert(mock_log.d).called_once_with('Bad length. Expected:% Actual:b')


    @patch('src.kprotocol.KermitPacket')
    @patch('src.kprotocol.log')
    def test_should_return_none_for_bad_length3(self, mock_log, mock_kp):
        buf = self.buf3
        k = src.kprotocol.KermitProtocol(Mock())
        mock_kp.return_value.length.return_value = 'c'

        sert(k.to_packet(buf, 3)).to_equal(None)
        sert(mock_log.d).called_once_with('Bad length. Expected:& Actual:c')


    @patch('src.kprotocol.KermitPacket')
    @patch('src.kprotocol.log')
    def test_should_return_none_for_bad_checksum1(self, mock_log, mock_kp):
        buf = self.buf1
        k = src.kprotocol.KermitProtocol(Mock())
        mock_kp.return_value.length.return_value = '$'
        mock_kp.return_value.checksum.return_value = 'x'

        sert(k.to_packet(buf, 1)).to_equal(None)
        sert(mock_log.d).called_once_with('Bad checksum. Expected:L Actual:x')


    @patch('src.kprotocol.KermitPacket')
    @patch('src.kprotocol.log')
    def test_should_return_none_for_bad_checksum2(self, mock_log, mock_kp):
        buf = self.buf2
        k = src.kprotocol.KermitProtocol(Mock())
        mock_kp.return_value.length.return_value = '%'
        mock_kp.return_value.checksum.return_value = 'x'

        sert(k.to_packet(buf, 2)).to_equal(None)
        sert(mock_log.d).called_once_with("Bad checksum. Expected:['#', 'J'] Actual:x")


    @patch('src.kprotocol.KermitPacket')
    @patch('src.kprotocol.log')
    def test_should_return_none_for_bad_checksum3(self, mock_log, mock_kp):
        buf = self.buf3
        k = src.kprotocol.KermitProtocol(Mock())
        mock_kp.return_value.length.return_value = '&'
        mock_kp.return_value.checksum.return_value = 'x'

        sert(k.to_packet(buf, 3)).to_equal(None)
        sert(mock_log.d).called_once_with("Bad checksum. Expected:[')', '1', '['] Actual:x")



class TestKermitProtocolWriteVerify(unittest.TestCase):

    @patch('src.kprotocol.log')
    def test_should_return_none(self, mock_log):
        pkt = paket('B')
        k = src.kprotocol.KermitProtocol(Mock())
        k.write_packet = Mock()
        k.read_any_packet = Mock(return_value=None)

        sert(k._write_verify(pkt)).to_equal(None)


    @patch('src.kprotocol.log')
    def test_should_ignore_response(self, mock_log):
        ignore_response = True
        pkt = paket('B')
        k = src.kprotocol.KermitProtocol(Mock())
        k.write_packet = Mock()
        k.read_any_packet = Mock()

        sert(k._write_verify(pkt, ignore_response)).to_equal(None)
        sert(k.read_any_packet).not_called()


    @patch('src.kprotocol.log')
    def test_should_retry_default_times(self, mock_log):
        pkt = paket('B')
        k = src.kprotocol.KermitProtocol(Mock())
        k.write_packet = Mock()
        k.read_any_packet = Mock(return_value=None)

        k._write_verify(pkt)

        sert(k.write_packet).called_n_times(5)
        sert(k.read_any_packet).called_n_times(5)


    @patch('src.kprotocol.log')
    def test_should_retry_specified_time(self, mock_log):
        pkt = paket('B')
        k = src.kprotocol.KermitProtocol(Mock())
        k.write_packet = Mock()
        k.read_any_packet = Mock(return_value=None)
        num = 7

        sert(k._write_verify(pkt, False, num)).to_equal(None)
        sert(k.write_packet).called_n_times(num)
        sert(k.read_any_packet).called_n_times(num)


    @patch('src.kprotocol.log')
    def test_should_retry_when_nack_returned(self, mock_log):
        pkt = paket('B')
        k = src.kprotocol.KermitProtocol(Mock())
        k.write_packet = Mock()
        k.read_any_packet = Mock(return_value=paket('N'))

        sert(k._write_verify(pkt)).to_equal(None)
        sert(mock_log.d).called_n_times(5)
        sert(mock_log.d).nth_call_called_with(1, 'Retrying')


    @patch('src.kprotocol.log')
    def test_should_return_error_packet(self, mock_log):
        pkt = paket('B')
        k = src.kprotocol.KermitProtocol(Mock())
        k.write_packet = Mock()
        k.read_any_packet = Mock(return_value=paket('E'))

        p = k._write_verify(pkt)

        sert(p.type).to_equal('E')


    @patch('src.kprotocol.log')
    def test_should_return_packet_with_same_seq_ch(self, mock_log):
        pkt_snd = paket('B')
        pkt_rcv = paket('Z')
        k = src.kprotocol.KermitProtocol(Mock())
        k.write_packet = Mock()
        k.read_any_packet = Mock(return_value=pkt_rcv)

        p = k._write_verify(pkt_snd)

        sert(p.type).to_equal('Z')
        sert(p.seq_ch).to_equal('&')


    @patch('src.kprotocol.log')
    def test_should_return_none_when_different_seq_ch(self, mock_log):
        pkt_snd = paket('B')
        pkt_snd.seq_ch = '%'
        pkt_rcv = paket('B')
        pkt_rcv.seq_ch = '$'
        k = src.kprotocol.KermitProtocol(Mock())
        k.write_packet = Mock()
        k.read_any_packet = Mock(return_value=pkt_rcv)

        sert(k._write_verify(pkt_snd)).to_equal(None)



class TestKermitProtocolIsResend(unittest.TestCase):

    def test_should_return_none(self):
        prev_pkt = None
        pkt = paket('B')
        k = src.kprotocol.KermitProtocol(Mock())

        sert(k._is_resend(prev_pkt, pkt)).to_equal(None)


    def test_should_be_true_for_matching_type_and_seq_ch(self):
        prev_pkt = paket('B')
        pkt = paket('B')
        k = src.kprotocol.KermitProtocol(Mock())
        sert(prev_pkt.seq_ch).to_equal(pkt.seq_ch)

        sert(k._is_resend(prev_pkt, pkt)).is_true()


    def test_should_be_false_for_mismatch_seq_ch(self):
        prev_pkt = paket('B', '%')
        pkt = paket('B', '$')
        k = src.kprotocol.KermitProtocol(Mock())
        sert(prev_pkt.seq_ch).not_equal(pkt.seq_ch)

        sert(k._is_resend(prev_pkt, pkt)).is_false()


    def test_should_be_false_for_mismatch_type(self):
        prev_pkt = paket('Z')
        pkt = paket('B')
        k = src.kprotocol.KermitProtocol(Mock())
        sert(prev_pkt.type).not_equal(pkt.type)

        sert(k._is_resend(prev_pkt, pkt)).is_false()



class TestKermitProtocolIsNextSeq(unittest.TestCase):

    def test_should_return_true_when_no_prev_packet(self):
        k = src.kprotocol.KermitProtocol(Mock())

        for i in range(0, 256):
            pkt = paket(chr(i))
            sert(k._is_next_seq(None, pkt)).is_true()


    @patch('src.kprotocol.log')
    def test_should_log_debug(self, mock_log):
        k = src.kprotocol.KermitProtocol(Mock())

        for i in range(0, 256):
            mock_log.reset_mock()
            ch = chr(i)
            k._is_next_seq(None, paket(ch))
            if ch in 'ISGECNR':
                sert(mock_log.d).not_called()
            else:
                sert(mock_log.d).called_once_with('Bad type. Expected one of "ISGECNR". Actual:{}'.format(ch))


    def test_should_return_true_for_sequential(self):
        max_seq = 64
        k = src.kprotocol.KermitProtocol(Mock())

        prev_pkt = paket('B')
        pkt = paket('B')
        for i in range(0, 3 * max_seq):
            prev_pkt.seq_ch = toCh(i % max_seq)
            pkt.seq_ch = toCh((i + 1) % max_seq)

            sert(k._is_next_seq(prev_pkt, pkt)).is_true()


    def test_should_return_false_for_non_sequential(self):
        max_seq = 64
        k = src.kprotocol.KermitProtocol(Mock())

        prev_pkt = paket('B')
        pkt = paket('B')
        for i in range(0, max_seq):
            for n in range(1, max_seq):
                prev_pkt.seq_ch = toCh(i)
                pkt.seq_ch = toCh((i + n + 1) % max_seq)

                sert(k._is_next_seq(prev_pkt, pkt)).is_false()


    @patch('src.kprotocol.log')
    def test_should_log_unexpected_packet_type(self, mock_log):
        prev_pkt = paket('_', ' ')
        pkt = paket('_', '!')
        states = {
            'S': 'FX',
            'F': 'D',
            'D': 'DZ',
            'Z': 'BF',
            'B': 'IS',
            'X': 'D',
        }
        k = src.kprotocol.KermitProtocol(Mock())

        for ch in states.keys():
            for n in range(0, 256):
                mock_log.reset_mock()
                prev_pkt.type = ch
                pkt.type = chr(n)

                sert(k._is_next_seq(prev_pkt, pkt)).is_true()
                if pkt.type not in states[prev_pkt.type] + 'NE':
                    sert(mock_log.d).called_once_with('Bad type. Expected:{}  Actual:{}'.format(states[prev_pkt.type], pkt.type))


    @patch('src.kprotocol.log')
    def test_should_log_unexpected_prev_packet_state(self, mock_log):
        prev_pkt = paket('I', toCh(33))
        pkt = paket('B', toCh(34))
        k = src.kprotocol.KermitProtocol(Mock())

        for i in range(0, 256):
            mock_log.reset_mock()
            ch = chr(i)
            prev_pkt.type = ch
            sert(k._is_next_seq(prev_pkt, pkt)).is_true()
            if ch not in 'BDFSXZ':
                sert(mock_log.d).called_once_with("Previous pkt type {} not in states ['B', 'D', 'F', 'S', 'X', 'Z']".format(ch))



class TestKermitProtocolDoAck(unittest.TestCase):

    @patch('src.kprotocol.P', new=Mock())
    @patch('src.kprotocol.log')
    def test_should_log_message_for_invalid_seq(self, mock_log):
        k = src.kprotocol.KermitProtocol(Mock())
        k.set_receive_params = Mock()
        k.write_packet = Mock()

        for typ in 'IS':
            for i in range(0, 64):
                mock_log.reset_mock()
                pkt = paket(typ, toCh(i))

                k._do_ack(pkt)

                if i == 0:
                    sert(mock_log.d).not_called()
                else:
                    sert(mock_log.d).called_once_with('Bad initial seq. Expected:0 Actual:{}'.format(i))


    @patch('src.kprotocol.P', new=Mock())
    @patch('src.kprotocol.log')
    def test_should_set_receive_parameters(self, mock_log):
        k = src.kprotocol.KermitProtocol(Mock())
        k.set_receive_params = Mock()
        k.write_packet = Mock()

        for typ in [chr(i) for i in range(0, 256)]:
            k.set_receive_params.reset_mock()
            pkt = paket(typ, toCh(0))

            k._do_ack(pkt)

            if typ in 'IS':
                sert(k.set_receive_params).called_once()
            else:
                sert(k.set_receive_params).not_called()


    @patch('src.kprotocol.P')
    @patch('src.kprotocol.log')
    def test_should_construct_ack_packet(self, mock_log, mock_p):
        init_params = 'abcd'
        k = src.kprotocol.KermitProtocol(Mock())
        k.set_receive_params = Mock()
        k.write_packet = Mock()
        k.get_init_params = Mock(return_value=init_params)

        for typ in [chr(i) for i in range(0, 256)]:
            mock_p.reset_mock()
            pkt = paket(typ)

            k._do_ack(pkt)

            args = mock_p.return_value.ack.call_args_list[0][0]
            if typ in 'IS':
                sert(len(args)).to_equal(2)
                sert(args[0].type).to_equal(typ)
                sert(args[1]).to_equal(init_params)
            elif typ == 'G':
                pass # This case handled by 'construct_ack_packet_for_g'.
            else:
                sert(len(args)).to_equal(1)
                sert(args[0].type).to_equal(typ)


    @patch('src.kprotocol.P')
    @patch('src.kprotocol.log')
    def test_should_construct_ack_packet_for_g(self, mock_log, mock_p):
        k = src.kprotocol.KermitProtocol(Mock())
        k.set_receive_params = Mock()
        k.write_packet = Mock()

        pkt = paket('G')
        for payload in 'FL':
            pkt.payload = [payload]

            k._do_ack(pkt)

            args = mock_p.return_value.ack.call_args_list[0][0]
            sert(len(args)).to_equal(2)
            sert(args[0].type).to_equal('G')
            sert(args[1]).to_equal('Goodbye')


    @patch('src.kprotocol.P')
    @patch('src.kprotocol.log')
    def test_should_write_ack_packet(self, mock_log, mock_p):
        k = src.kprotocol.KermitProtocol(Mock())
        k.set_receive_params = Mock()
        k.write_packet = Mock()
        mock_p.return_value.ack.return_value = 'ackPkt'

        for typ in [chr(i) for i in range(0, 256)]:
            k.write_packet.reset_mock()
            pkt = paket(typ)

            k._do_ack(pkt)

            sert(k.write_packet).called_once_with('ackPkt')



class TestKermitProtocolNack(unittest.TestCase):

    @patch('src.kprotocol.P')
    def test_should_write_nack_packet(self, mock_p):
        nack_pkt = 'nackPkt'
        k = src.kprotocol.KermitProtocol(Mock())
        k.write_packet = Mock()
        mock_p.return_value.nack.return_value = nack_pkt
        pkt = paket('B')

        k._do_nack(pkt)

        sert(k.write_packet).called_once_with(nack_pkt)



class TestKermitProtocolIsInitPkt(unittest.TestCase):

    def test_should_te_finish_packet(self):
        k = src.kprotocol.KermitProtocol(Mock())
        for typ in [chr(i) for i in range(0, 256)]:
            pkt = paket(typ)

            ans = k._is_init_pkt(pkt)

            if typ == 'I':
                sert(ans).is_true()
            else:
                sert(ans).is_false()



class TestKermitProtocolFinish(unittest.TestCase):

    @patch('src.kprotocol.P')
    def test_should_write_finish_packet(self, mock_p):
        finish_pkt = 'finishPkt'
        k = src.kprotocol.KermitProtocol(Mock())
        k.write_packet = Mock()
        mock_p.return_value.finish.return_value = finish_pkt
        pkt = paket('B')

        k._finish()

        sert(k.write_packet).called_once_with(finish_pkt)



class TestKermitProtocolGet(unittest.TestCase):

    @patch('src.kprotocol.P')
    def test_should_get(self, mock_p):
        pkt = 'aPkt'
        name = 'aname'
        k = src.kprotocol.KermitProtocol(Mock())
        k._send_then_receive = Mock()
        mock_p.return_value.receive_initiate.return_value = pkt

        k._get(name)

        sert(mock_p.return_value.receive_initiate).called_once_with(name)
        sert(k._send_then_receive).called_once_with(pkt)



class TestKermitProtocolSaveBufData(unittest.TestCase):

    @patch('src.kprotocol.log')
    def test_should_log_data(self, mock_log):
        k = src.kprotocol.KermitProtocol(Mock())
        name = None
        data = ['a', 'b', 'c']

        k._save_buf_data(name, data)

        sert(mock_log.i).called_once_with('abc')


    @patch('src.kprotocol.log')
    @patch('src.kprotocol.os')
    @patch('__builtin__.open')
    def test_should_save_data_as_name(self, mock_open, mock_os, mock_log):
        k = src.kprotocol.KermitProtocol(Mock())
        mock_os.path.isfile.return_value = False
        name = 'name.txt'
        data = ['a', 'b', 'c']

        k._save_buf_data(name, data)

        sert(mock_open).called_once_with(name, 'wb')
        sert(mock_open.return_value.write).called_once_with(bytearray(data))
        sert(mock_open.return_value.close).called_once()


    @patch('src.kprotocol.log')
    @patch('src.kprotocol.os')
    @patch('__builtin__.open')
    def test_should_save_data_as_new_name(self, mock_open, mock_os, mock_log):
        k = src.kprotocol.KermitProtocol(Mock())
        mock_os.path.isfile.side_effect = [True, True, False]
        name = 'name.txt'
        data = ['a', 'b', 'c']

        k._save_buf_data(name, data)

        sert(mock_open).called_once_with(name + '.2', 'wb')
        sert(mock_open.return_value.write).called_once_with(bytearray(data))
        sert(mock_open.return_value.close).called_once()


    @patch('src.kprotocol.log')
    @patch('src.kprotocol.os')
    @patch('__builtin__.open')
    def test_should_log_name_when_config_is_off_and_file_renamed(self, mock_open, mock_os, mock_log):
        k = src.kprotocol.KermitProtocol(Mock())
        mock_os.path.isfile.side_effect = [True, True, True, False]
        k.config['warning'].value = 0

        k._save_buf_data('name.txt', ['a', 'b', 'c'])

        sert(mock_log.i).called_once_with('Wrote name.txt.3')


    @patch('src.kprotocol.log')
    @patch('src.kprotocol.os')
    @patch('__builtin__.open')
    def test_should_log_rename_when_config_is_on_and_file_renamed(self, mock_open, mock_os, mock_log):
        k = src.kprotocol.KermitProtocol(Mock())
        mock_os.path.isfile.side_effect = [True, True, True, False]
        k.config['warning'].value = 1

        k._save_buf_data('name.txt', ['a', 'b', 'c'])

        sert(mock_log.i).called_once_with('Wrote name.txt as name.txt.3')


    @patch('src.kprotocol.log')
    @patch('src.kprotocol.os')
    @patch('__builtin__.open')
    def test_should_log_name_when_config_is_off_and_no_rename(self, mock_open, mock_os, mock_log):
        name = 'name.txt'
        k = src.kprotocol.KermitProtocol(Mock())
        mock_os.path.isfile.return_value = False
        k.config['warning'].value = 0

        k._save_buf_data(name, ['a', 'b', 'c'])

        sert(mock_log.i).called_once_with('Wrote {}'.format(name))


    @patch('src.kprotocol.log')
    @patch('src.kprotocol.os')
    @patch('__builtin__.open')
    def test_should_log_name_when_config_is_on_and_no_rename(self, mock_open, mock_os, mock_log):
        k = src.kprotocol.KermitProtocol(Mock())
        mock_os.path.isfile.return_value = False
        k.config['warning'].value = 1
        name = 'name.txt'

        k._save_buf_data(name, ['a', 'b', 'c'])

        sert(mock_log.i).called_once_with('Wrote {}'.format(name))



k = None



class TestKermitProtocolServer(unittest.TestCase):

    def setUp(self):
        global k
        self.kermit = src.kprotocol.KermitProtocol(Mock())
        k = self.kermit
        k._is_resend = Mock(return_value=False)
        k._is_init_pkt = Mock(return_value=False)
        k._is_next_seq = Mock(return_value=True)
        k._do_ack = Mock()
        k._do_nack = Mock()


    @patch('src.kprotocol.log')
    def test_should_log(self, mock_log):
        k.read_any_packet = Mock(side_effect=[None, term_pkt()])

        k._server()

        sert(mock_log.d).called_once_with('No packet read')


    @patch('src.kprotocol.log')
    def test_should_ack_on_resend(self, mock_log):
        pkt = paket('D')
        k._is_resend = Mock(side_effect=[True, False])
        k.read_any_packet = Mock(side_effect=[pkt, term_pkt()])

        k._server()

        sert(k._do_ack).called_twice()
        sert(k._do_ack.mock_calls[0].args[0].type).to_equal('D')
        sert(k._do_ack.mock_calls[1].args[0].type).to_equal('G')


    @patch('src.kprotocol.log')
    def test_should_ack_on_init(self, mock_log):
        pkt = paket('D')
        k._is_init_pkt = Mock(side_effect=[True, False])
        k.read_any_packet = Mock(side_effect=[pkt, term_pkt()])

        k._server()

        sert(k._do_ack).called_twice()
        sert(k._do_ack.mock_calls[0].args[0].type).to_equal('D')
        sert(k._do_ack.mock_calls[1].args[0].type).to_equal('G')


    @patch('src.kprotocol.log')
    def test_should_nack_on_bad_sequence(self, mock_log):
        pkt = paket('D')
        k._is_next_seq = Mock(side_effect=[False, True])
        k.read_any_packet = Mock(side_effect=[pkt, term_pkt()])

        k._server()

        sert(k._do_nack).called_once()
        sert(k._do_nack.mock_calls[0].args[0].type).to_equal('D')
        sert(k._do_ack).called_once()
        sert(k._do_ack.mock_calls[0].args[0].type).to_equal('G')


    @patch('src.kprotocol.log')
    def test_should_receive_params_on_s_packet(self, mock_log):
        pkt = paket('S')
        k.set_receive_params = Mock()
        k.read_any_packet = Mock(side_effect=[pkt, term_pkt()])

        k._server()

        sert(k.set_receive_params).called_once()
        sert(k.set_receive_params.mock_calls[0].args[0].type).to_equal('S')
        sert(k._do_ack).called_twice()
        sert(k._do_ack.mock_calls[0].args[0].type).to_equal('S')
        sert(k._do_ack.mock_calls[1].args[0].type).to_equal('G')


    def test_should_terminate_on_zero_nack(self):
        pkt = paket('N', toCh(0))
        pkt.payload = []
        k.read_any_packet = Mock(side_effect=[pkt])

        k._server()

        sert(k._do_ack).not_called()


    def test_should_continue_on_non_zero_nack(self):
        for i in range(1, 64):
            k._do_ack.reset_mock()
            pkt = paket('N', toCh(i))
            k.read_any_packet = Mock(side_effect=[pkt, term_pkt()])

            k._server()

            sert(k._do_ack).called_once()
            sert(k._do_ack.mock_calls[0].args[0].type).to_equal('G')


    def test_should_finish(self):
        pkt = paket('G')
        pkt.payload = ['F']
        k.read_any_packet = Mock(side_effect=[pkt])

        k._server()

        sert(k._do_ack).called_twice()
        sert(k._do_ack.mock_calls[0].args[0].type).to_equal('G')


    def test_should_logout(self):
        pkt = paket('G')
        pkt.payload = ['L']
        k.read_any_packet = Mock(side_effect=[pkt])

        k._server()

        sert(k._do_ack).called_once()
        sert(k._do_ack.mock_calls[0].args[0].type).to_equal('G')


    @patch('src.kprotocol.log')
    def test_should_display_message(self, mock_log):
        pkt = paket('G')
        pkt.payload = ['M', ':', 'S', 'o', 'm', 'e', ' ', 't', 'e', 'x', 't']
        k.read_any_packet = Mock(side_effect=[pkt, term_pkt()])

        k._server()

        sert(mock_log.i).called_once_with('Message: Some text')


    def test_should_show_server_info(self):
        pkt = paket('G')
        pkt.payload = ['I']
        k._send_bytes = Mock()
        k.read_any_packet = Mock(side_effect=[pkt, term_pkt()])

        k._server()

        sert(k._send_bytes).called_once_with(None, 'HpirComm Server')


    def test_should_ack_g_packets(self):
        pkt = paket('G')
        k._send_bytes = Mock()
        k.read_any_packet = Mock(side_effect=[pkt, term_pkt()])

        k._server()

        sert(k._do_ack).called_twice()
        sert(k._do_ack.mock_calls[0].args[0].type).to_equal('G')
        sert(k._do_ack.mock_calls[1].args[0].type).to_equal('G')


    def test_should_nack_an_empty_f_packet(self):
        pkt = paket('F')
        pkt.payload = []
        k.read_any_packet = Mock(side_effect=[pkt, term_pkt()])

        k._server()

        sert(k._do_nack).called_once()
        sert(k._do_nack.mock_calls[0].args[0].type).to_equal('F')


    def test_should_handle_d_and_z_packet(self):
        dat = ['d', 'a', 't', 'a']
        data_pkt = paket('D')
        data_pkt.payload = dat
        pkt = paket('Z')
        k._save_buf_data = Mock()
        k.read_any_packet = Mock(side_effect=[data_pkt, pkt, term_pkt()])

        k._server()

        # In code under test, the buffer (in_buf) is cleared, so we lose the
        # elements of dat, resulting in an empty array.
        sert(k._save_buf_data).called_once_with(None, [])
        sert(k._do_ack).called_n_times(3)
        sert(k._do_ack.mock_calls[0].args[0].type).to_equal('D')
        sert(k._do_ack.mock_calls[1].args[0].type).to_equal('Z')


    def test_should_handle_f_and_d_and_z_packet(self):
        name = ['a', 'b', '.', 't', 'x', 't']
        name_pkt = paket('F')
        name_pkt.payload = name
        dat = ['d', 'a', 't', 'a']
        data_pkt = paket('D')
        data_pkt.payload = dat
        pkt = paket('Z')
        k._save_buf_data = Mock()
        k.read_any_packet = Mock(side_effect=[name_pkt, data_pkt, pkt, term_pkt()])

        k._server()

        # In code under test, the buffer (in_buf) is cleared, so we lose the
        # elements of dat, resulting in an empty array.
        sert(k._save_buf_data).called_once_with('ab.txt', [])
        sert(k._do_ack).called_n_times(4)
        sert(k._do_ack.mock_calls[0].args[0].type).to_equal('F')
        sert(k._do_ack.mock_calls[1].args[0].type).to_equal('D')
        sert(k._do_ack.mock_calls[2].args[0].type).to_equal('Z')


    def test_should_handle_z_packet_without_data(self):
        pkt = paket('Z')
        k._save_buf_data = Mock()
        k.read_any_packet = Mock(side_effect=[pkt, term_pkt()])

        k._server()

        sert(k._save_buf_data).not_called()
        sert(k._do_ack).called_twice()
        sert(k._do_ack.mock_calls[0].args[0].type).to_equal('Z')


    @patch('src.kprotocol.log')
    @patch('src.kprotocol.subprocess')
    def test_should_handle_c_packet(self, mock_subprocess, mock_log):
        cmd = 'a cmd'
        stdout_txt = 'stdoutTxt'
        pkt = paket('C')
        pkt.payload = cmd
        k._send_bytes = Mock()
        k.read_any_packet = Mock(side_effect=[pkt, term_pkt()])
        mock_subprocess.Popen.return_value.communicate.return_value=(stdout_txt, 'stderrTxt')

        k._server()

        sert(mock_log.i).called_twice()
        sert(mock_log.i).first_call_called_with('Executing cmd: {}'.format(cmd))
        sert(mock_log.i).second_call_called_with(stdout_txt)
        sert(k._send_bytes).called_once_with(None, stdout_txt)


    def test_should_handle_r_packet(self):
        payload = 'data'
        pkt = paket('R')
        pkt.payload = [payload]
        k._send_file = Mock()
        k.read_any_packet = Mock(side_effect=[pkt, term_pkt()])

        k._server()

        sert(k._send_file).called_once_with(payload, False)


    def test_should_handle_b_packet(self):
        pkt = paket('B')
        k.read_any_packet = Mock(side_effect=[pkt, term_pkt()])

        k._server()

        sert(k._do_ack).called_twice()
        sert(k._do_ack.mock_calls[0].args[0].type).to_equal('B')


    def test_should_exit_on_eot(self):
        exit_on_eot = True
        pkt = paket('B')
        k.read_any_packet = Mock(side_effect=[pkt])

        k._server(exit_on_eot)

        sert(k._do_ack).called_once()
        sert(k._do_ack.mock_calls[0].args[0].type).to_equal('B')


    def test_should_handle_x_packet(self):
        pkt = paket('X')
        k.read_any_packet = Mock(side_effect=[pkt, term_pkt()])

        k._server()

        sert(k._do_ack).called_twice()
        sert(k._do_ack.mock_calls[0].args[0].type).to_equal('X')


    @patch('src.kprotocol.log')
    def test_should_handle_e_packet(self, mock_log):
        payload = 'data'
        pkt = paket('E')
        pkt.payload = payload
        k.read_any_packet = Mock(side_effect=[pkt, term_pkt()])

        k._server()

        sert(mock_log.i).called_once_with('Remote error: {}'.format(payload))


    @patch('src.kprotocol.log')
    def test_should_log_unhandled_packet_type(self, mock_log):
        pkt = paket('_')
        k.read_any_packet = Mock(side_effect=[pkt, term_pkt()])

        k._server()

        sert(mock_log.d).called_once_with('Unhandled packet:_&1')



class TestKermitProtocolSendCommand(unittest.TestCase):

    @patch('src.kprotocol.log')
    def test_should_log_error(self, mock_log):
        k = src.kprotocol.KermitProtocol(Mock())
        k._write_verify = Mock(return_value=None)

        k.send_command('cmd1')

        sert(mock_log.e).called_once_with('Failed to send command cmd1')


    def test_should_send_command(self):
        buf = bytearray('xxxC')
        mock_transport = Mock()
        mock_transport.peek_bytes.return_value = buf
        mock_transport.read_bytes.return_value = buf
        k = src.kprotocol.KermitProtocol(mock_transport)
        k._write_verify = Mock()
        k._receive = Mock()
        k._poll_bytes_ready = Mock(return_value=len(buf))
        cmd = 'cmd1'

        k.send_command(cmd)

        sert(k._write_verify).called_once()
        args, kwargs = k._write_verify.call_args_list[0]
        sert(args[0].payload).to_equal(cmd)


    def test_should_handle_nack_response(self):
        mock_transport = Mock()
        pkt_x = paket('X')
        k = src.kprotocol.KermitProtocol(mock_transport)
        k._write_verify = Mock(side_effect=[paket('N'), pkt_x])
        k._receive = Mock()

        k.send_command('cmd1')

        sert(k._write_verify).called_twice()
        sert(k._receive).called_once_with(pkt_x)



def paket(typ, s_ch='&', bc=1, payload=''): # Intentionally misspelled.
    '''Bare-bones packet'''
    obj = Mock()
    obj.type = typ
    obj.seq_ch = s_ch
    obj.blockcheck = bc
    obj.payload = payload
    obj.to_list = Mock(return_value=''.join([obj.type, obj.seq_ch, str(obj.blockcheck), str(obj.payload)]))
    return obj


def term_pkt(): # A packet which will terminate the server.
    return paket('G', ' ', 1, 'L')


def toCh(i):
    return chr(i + 32)



class TestKermitProtocolIsPrefix(unittest.TestCase):

    def test_should_be_true_for_default_prefix(self):
        k = src.kprotocol.KermitProtocol(Mock())
        sert(k.is_prefix('#')).is_true()


    def test_should_false_for_non_prefix(self):
        k = src.kprotocol.KermitProtocol(Mock())
        for i in range(0, 256):
            if chr(i & 0x7F) == '#':
                continue
            ch = chr(i)
            sert(k.is_prefix(ch)).is_false()


    def test_should_be_true_for_configured_prefix(self):
        pfx = '@'
        k = src.kprotocol.KermitProtocol(Mock())
        k.config['send']['ctl-prefix'].value = pfx
        sert(k.is_prefix(pfx)).is_true()



class TestKermitProtocolUnescapePayload(unittest.TestCase):

    def test_should_unescape_payload(self):
        k = src.kprotocol.KermitProtocol(Mock())
        sert(k._unescape_payload('abc')).to_equal(['a', 'b', 'c'])


    @patch('src.kprotocol.log')
    def test_should_unescape_invalid_payload(self, mock_log):
        k = src.kprotocol.KermitProtocol(Mock())
        sert(k._unescape_payload('ab#')).to_equal(['a', 'b'])
        sert(mock_log.e).called_once_with('Bad payload length')


    def test_should_handle_prefix(self):
        k = src.kprotocol.KermitProtocol(Mock())
        for i in range(0, 63):
            ch = chr(i)
            sert(k._unescape_payload('ab#'+ch)).to_equal(['a', 'b', ch])

        for i in range(63, 96):
            ch = chr(i)
            aa = chr(i ^ 64)
            sert(k._unescape_payload('ab#'+ch)).to_equal(['a', 'b', aa])

        for b in range(96, 191):
            i = b & 0x7F
            ch = chr(i)
            sert(k._unescape_payload('ab#'+ch)).to_equal(['a', 'b', ch])

        for b in range(191, 224):
            i = b & 0x7F
            ch = chr(i)
            aa = chr(i ^ 64)
            sert(k._unescape_payload('ab#'+ch)).to_equal(['a', 'b', aa])

        for b in range(224, 256):
            i = b & 0x7F
            ch = chr(i)
            sert(k._unescape_payload('ab#'+ch)).to_equal(['a', 'b', ch])



class TestKermitProtocolConstructPayloads(unittest.TestCase):

    def test_should_construct_payloads(self):
        k = src.kprotocol.KermitProtocol(Mock())
        sert(k.construct_payloads('', '#', 8)).to_equal([])
        sert(k.construct_payloads('abc', '#', 8)).to_equal([['a', 'b', 'c']])
        sert(k.construct_payloads('abcdefgh', '#', 4)).to_equal([['a', 'b', 'c', 'd'], ['e', 'f', 'g', 'h']])


    def test_should_add_prefix(self):
        prefix_char = '#'
        k = src.kprotocol.KermitProtocol(Mock())
        sert(k.construct_payloads('ab\x88', prefix_char, 8)).to_equal([['a', 'b', prefix_char, '\xc8']])
        sert(k.construct_payloads('ab'+prefix_char, prefix_char, 8)).to_equal([['a', 'b', prefix_char, prefix_char]])



class TestKermitProtocolSendAbort(unittest.TestCase):

    def test_should_send_abort(self):
        k = src.kprotocol.KermitProtocol(Mock())
        k.write_packet = Mock()

        k.send_abort()

        sert(k.write_packet).called_n_times(3)
        for args, kwargs in k.write_packet.call_args_list:
            pkt = args[0]
            sert(pkt.type).to_equal('E')
            sert(pkt.payload).to_equal('Abort')



class TestKermitProtocolBytesToPackets(unittest.TestCase):

    def test_should_construct_file_packets(self):
        k = src.kprotocol.KermitProtocol(Mock())
        k.write_packet = Mock()

        packets = k._bytes_to_packets('filename', 'data')

        sert(len(packets)).to_equal(5)
        sert(packets[0].type).to_equal('S')
        sert(packets[1].type).to_equal('F')
        sert(packets[2].type).to_equal('D')
        sert(packets[3].type).to_equal('Z')
        sert(packets[4].type).to_equal('B')


    def test_should_construct_text_packets(self):
        k = src.kprotocol.KermitProtocol(Mock())
        k.write_packet = Mock()

        packets = k._bytes_to_packets(None, 'data')

        sert(len(packets)).to_equal(5)
        sert(packets[0].type).to_equal('S')
        sert(packets[1].type).to_equal('X')
        sert(packets[2].type).to_equal('D')
        sert(packets[3].type).to_equal('Z')
        sert(packets[4].type).to_equal('B')


    def test_should_construct_multiple_data_packets(self):
        packet_len = 20
        k = src.kprotocol.KermitProtocol(Mock())
        k.config['send']['packet-length'].value = packet_len
        data = 'x' * packet_len * 3
        k.write_packet = Mock()

        packets = k._bytes_to_packets(None, data)

        sert(len(packets)).to_equal(8)
        sert(packets[0].type).to_equal('S')
        sert(packets[1].type).to_equal('X')
        sert(packets[2].type).to_equal('D')
        sert(packets[3].type).to_equal('D')
        sert(packets[4].type).to_equal('D')
        sert(packets[5].type).to_equal('D')
        sert(packets[6].type).to_equal('Z')
        sert(packets[7].type).to_equal('B')



class TestKermitProtocolSendPackets(unittest.TestCase):

    def test_should_send_packets(self):
        ignore_response = False
        k = src.kprotocol.KermitProtocol(Mock())
        k._write_verify = Mock(return_value=paket('_'))
        k.config['ignorerx'].value = ignore_response
        p1 = paket('N')

        ans = k._send_packets([p1])

        sert(ans).is_true()
        sert(k._write_verify).called_once_with(p1, ignore_response)


    def test_should_retry(self):
        k = src.kprotocol.KermitProtocol(Mock())
        k._write_verify = Mock(return_value=None)

        ans = k._send_packets([paket('_')])

        sert(ans).is_false()
        sert(k._write_verify).called_n_times(7)


    def test_should_set_receive_params_after_sending_s_packet(self):
        k = src.kprotocol.KermitProtocol(Mock())
        wv_pkt = paket('_')
        k._write_verify = Mock(return_value=wv_pkt)
        k.set_receive_params = Mock()

        ans = k._send_packets([ paket('S') ])

        sert(ans).is_true()
        sert(k.set_receive_params).called_once_with(wv_pkt)


    def test_should_handle_e_packet(self):
        k = src.kprotocol.KermitProtocol(Mock())
        k._write_verify = Mock(return_value=paket('E'))

        ans = k._send_packets([paket('_')])

        sert(ans).is_false()


    @patch('time.sleep')
    def test_should_ignore_response(self, mock_sleep):
        secs = 0.7
        k = src.kprotocol.KermitProtocol(Mock())
        k.config['ignorerx'].value = True
        k.config['ignore-sec'].value = secs

        ans = k._send_packets([paket('_')])

        sert(ans).is_true()
        sert(mock_sleep).called_once_with(secs)



class TestKermitProtocolSendBytes(unittest.TestCase):

    def test_should_send_bytes(self):
        k = src.kprotocol.KermitProtocol(Mock())
        k._send_packets = Mock()

        ans = k._send_bytes('name', 'some text')

        sert(ans).is_true()
        sert(k._send_packets).called_once()
        args, kwargs = k._send_packets.call_args_list[0]
        sert(len(args[0])).to_equal(5)


    def test_should_handle_keyboard_interrupt(self):
        k = src.kprotocol.KermitProtocol(Mock())
        k._send_packets = Mock(side_effect=KeyboardInterrupt)
        k.send_abort = Mock()

        ans = k._send_bytes('name', 'some text')

        sert(ans).is_false()
        sert(k.send_abort).called_once()
