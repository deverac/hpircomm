import unittest
from mock import patch, call, Mock, MagicMock

import src.log
import src.transport
import src.xmodem
from tests.sert import sert


xmod = None
transport_ary = []
tport = MagicMock(autospec=src.transport.Transport)
sleep_counter = 0


HEADER_BYTE = 0x01
END_TRANS   = 0x04
ACK         = 0x06
NACK        = 0x15
CANCEL      = 0x18


R_BLOCK = 101
R_ACK = 102
R_NACK = 103
R_CANCEL = 104
R_END_TRANS = 105
R_FAIL = 106


def make_block(seq, val_lst):
    block = [HEADER_BYTE, seq, 255-seq]
    pkt = val_lst
    pkt.extend((128 - len(val_lst)) * [0])
    block.extend(pkt)
    block.append(sum(pkt) % 256)
    return block


def fake_sleep(secs):
    global sleep_counter
    sleep_counter += 1
    #print 'sleepig'
    if sleep_counter > 1000:
        raise Exception('fake_sleep was called too many times')


def is_config(dct):
    return sorted(dct.keys()) == ['cpause', 'ignore-sec', 'ignorerx', 'init-wait', 'npoll', 'pad-char', 'pause', 'receive-retry', 'send-retry']


def is_cmds(dct):
    return sorted(dct.keys()) == ['help', 'quit', 'receive', 'send', 'set', 'show']


def is_const_dct(dct):
    return dct == {}


def is_log(mod):
    return mod.__name__ == 'src.log'



class TestNow(unittest.TestCase):

    @patch('time.time')
    def test_should_get_time(self, mock_time):
        src.xmodem.now()

        sert(mock_time.called_once())



class Base(unittest.TestCase):

    def setUp(self):
        global xmod
        global sleep_counter
        sleep_counter = 0
        del transport_ary[:]
        tport.reset_mock()
        tport.peek = Mock(return_value = transport_ary)
        tport.read = Mock(return_value = transport_ary)
        tport.read_bytes = Mock(return_value = transport_ary)
        xmod = src.xmodem.Xmodem(tport)



class TestNextSeq(Base):

    def test_should_return_next_seq(self):
        sert(xmod._next_seq(0)).to_equal(1)
        for i in range(1, 255):
            sert(xmod._next_seq(i)).to_equal(i+1)
        sert(xmod._next_seq(255)).to_equal(1)
        sert(xmod._next_seq(256)).to_equal(2)
        sert(xmod._next_seq(257)).to_equal(3)



class TestChecksum(Base):

    def test_should_return_checksum(self):
        sert(xmod._checksum([1, 2, 3, 4, 5])).to_equal(15)
        sert(xmod._checksum([256])).to_equal(0)
        sert(xmod._checksum([1, 2, 3, 4, 5, 256])).to_equal(15)



class TestSplitData(Base):

    def test_should_handle_empty_data(self):
        dat = []

        packets = xmod._split_data(dat)

        sert(len(packets)).to_equal(0)
        sert(packets).to_equal([])


    def test_should_create_block_with_padding(self):
        dat = 10 * [65]

        packets = xmod._split_data(dat)

        sert(len(packets)).to_equal(1)
        sert(len(packets[0])).to_equal(128)
        sert(packets[0]).to_equal((10 * [65]) + (118 * ['\x00']))


    def test_should_create_one_block(self):
        dat = 128 * [65]

        packets = xmod._split_data(dat)

        sert(len(packets)).to_equal(1)
        sert(len(packets[0])).to_equal(128)
        sert(packets[0]).to_equal(128 * [65])


    def test_should_create_two_blocks_with_padding(self):
        dat = 129 * [65]

        packets = xmod._split_data(dat)

        sert(len(packets)).to_equal(2)
        sert(len(packets[0])).to_equal(128)
        sert(len(packets[1])).to_equal(128)
        sert(packets[0]).to_equal(128 * [65])
        sert(packets[1]).to_equal((1 * [65]) + (127 * ['\x00']))



class TestConstructBlocks(Base):

    def test_should_construct_blocks(self):
        p1 = 128 * [65]
        p2 = 128 * [66]
        packets = [p1, p2]

        blocks = xmod._construct_blocks(packets)

        sert(len(blocks)).to_equal(2)
        sert(len(blocks)).to_equal(len(packets))

        b1 = blocks[0]
        sert(len(b1)).to_equal(132)
        sert(b1[0]).to_equal(HEADER_BYTE)
        sert(b1[1]).to_equal(1)
        sert(b1[2]).to_equal(254)
        sert(b1[3:131]).to_equal(p1)
        sert(b1[131]).to_equal(128)

        b2 = blocks[1]
        sert(len(b2)).to_equal(132)
        sert(b2[0]).to_equal(HEADER_BYTE)
        sert(b2[1]).to_equal(2)
        sert(b2[2]).to_equal(253)
        sert(b2[3:131]).to_equal(p2)
        sert(b2[131]).to_equal(0)



class TestExtractPacket(Base):

    def test_should_extract_packet(self):
        block = make_block(1, [65, 66])

        packet = xmod._extract_packet(block)

        sert(len(packet)).to_equal(128)
        sert(packet).to_equal([65, 66] + 126 * [0])



class TestIsValidBlock(Base):

    def test_should_be_false_for_bad_length(self):
        seq = 1
        block = [1, seq, 254]

        ans = xmod._is_valid_block(block, seq)

        sert(ans).is_false()


    def test_should_be_false_for_bad_header(self):
        seq = 1
        block = make_block(seq, [65])
        block[0] = 0x02

        ans = xmod._is_valid_block(block, seq)

        sert(ans).is_false()


    def test_should_be_false_for_bad_seq(self):
        seq = 1
        block = make_block(seq, [65])

        ans = xmod._is_valid_block(block, seq+1)

        sert(ans).is_false()


    def test_should_be_false_for_bad_comp_seq(self):
        seq = 1
        block = make_block(seq, [65])
        block[2] = seq + 1

        ans = xmod._is_valid_block(block, seq)

        sert(ans).is_false()


    def test_should_be_false_for_bad_checksum(self):
        seq = 1
        block = make_block(seq, [65])
        block[-1] = ((block[-1] + 1) % 256)

        ans = xmod._is_valid_block(block, seq)

        sert(ans).is_false()


    def test_should_be_true_for_valid_block(self):
        seq = 1
        block = make_block(seq, [65])

        ans = xmod._is_valid_block(block, seq)

        sert(ans).is_true()



class TestSendEndTrans(Base):

    @patch('time.sleep', new=fake_sleep)
    def test_should_send_end_trans(self):
        xmod._rcv_resp = Mock(return_value=R_ACK)

        ans = xmod._send_end_trans()

        sert(ans).is_true()
        sert(tport.write_byte).called_once_with(END_TRANS)


    @patch('time.sleep', new=fake_sleep)
    def test_should_return_false_when_retries_exceeded(self):
        retries = 3
        xmod.config['send-retry'].value = retries
        xmod._rcv_resp = Mock()

        ans = xmod._send_end_trans()

        sert(ans).is_false()
        sert(tport.write_byte).called_n_times(retries)
        sert(tport.write_byte).nth_call_called_with(1, END_TRANS)
        sert(tport.write_byte).nth_call_called_with(2, END_TRANS)
        sert(tport.write_byte).nth_call_called_with(3, END_TRANS)


    @patch('time.sleep', new=fake_sleep)
    def test_should_return_false_on_cancel(self):
        xmod._rcv_resp = Mock(return_value=R_CANCEL)

        ans = xmod._send_end_trans()

        sert(ans).is_false()


    @patch('time.sleep', new=fake_sleep)
    def test_should_succeed_after_multiple_retries(self):
        xmod._rcv_resp = Mock(side_effect=['', '', R_ACK])

        ans = xmod._send_end_trans()

        sert(ans).is_true()
        sert(tport.write_byte).called_n_times(3)
        sert(tport.write_byte).nth_call_called_with(1, END_TRANS)
        sert(tport.write_byte).nth_call_called_with(2, END_TRANS)
        sert(tport.write_byte).nth_call_called_with(3, END_TRANS)



class TestSendBytes(Base):

    @patch('time.sleep', new=fake_sleep)
    def test_should_return_true_on_ack(self):
        xmod._rcv_resp = Mock(side_effect=[R_NACK, R_ACK, R_ACK])
        data = [65, 66, 67]

        ans = xmod._send_bytes(bytearray(data))

        sert(ans).is_true()
        sert(tport.write_bytes).called_once_with(make_block(1, data))
        sert(tport.write_byte).called_once_with(END_TRANS)


    @patch('time.sleep', new=fake_sleep)
    def test_should_return_false_after_no_nack_and_max_retries(self):
        retries = 10
        xmod._rcv_resp = Mock(side_effect=([''] * retries))
        data = [65, 66, 67]

        ans = xmod._send_bytes(bytearray(data))

        sert(ans).is_false()


    @patch('time.sleep', new=fake_sleep)
    def test_should_return_false_on_cancel(self):
        xmod._rcv_resp = Mock(return_value=R_CANCEL)

        ans = xmod._send_bytes(bytearray([65, 66, 67]))

        sert(ans).is_false()


    @patch('time.sleep', new=fake_sleep)
    def test_should_return_false_when_retries_exceeded(self):
        retries = xmod.config['send-retry'].value
        xmod._rcv_resp = Mock(side_effect=[R_NACK] + ([R_FAIL] * (retries+1)))

        data = [65, 66, 67]

        ans = xmod._send_bytes(bytearray(data))

        sert(ans).is_false()
        sert(tport.write_bytes).called_n_times(retries + 2)
        block = make_block(1, data)
        sert(tport.write_bytes).nth_call_called_with(1, block) # Initial send
        sert(tport.write_bytes).nth_call_called_with(2, block) # Retry #1
        sert(tport.write_bytes).nth_call_called_with(3, block)
        sert(tport.write_bytes).nth_call_called_with(4, block)
        sert(tport.write_bytes).nth_call_called_with(5, block)
        sert(tport.write_bytes).nth_call_called_with(6, block) # Retry #5
        sert(tport.write_bytes).nth_call_called_with(7, [CANCEL, CANCEL, CANCEL])


    @patch('time.sleep', new=fake_sleep)
    def test_should_reset_retry_count_after_ack(self):
        xmod._rcv_resp = Mock(side_effect=[R_NACK, '', '', '', '', R_ACK, '', '', '', R_ACK, R_ACK])
        data = 200 * [65]

        ans = xmod._send_bytes(bytearray(data))

        sert(ans).is_true()
        sert(tport.write_bytes).called_n_times(9)
        sert(tport.write_byte).called_once_with(END_TRANS)


    @patch('time.sleep', new=fake_sleep)
    def test_should_return_false_on_cancel(self):
        xmod._rcv_resp = Mock(side_effect=[R_CANCEL])
        data = [65]

        ans = xmod._send_bytes(bytearray(data))

        sert(ans).is_false()


    @patch('time.sleep', new=fake_sleep)
    def test_should_return_false_on_cancel_after_nack(self):
        xmod._rcv_resp = Mock(side_effect=[R_NACK, R_CANCEL])
        data = [65]

        ans = xmod._send_bytes(bytearray(data))

        sert(ans).is_false()



class TestSendFile(Base):

    @patch('sys.stdin')
    def test_should_read_from_stdin(self, mock_stdin):
        filedata = 'abc'
        mock_stdin.read = Mock(return_value=filedata)
        xmod._send_bytes = Mock()

        xmod.send_file('STDIN')

        sert(xmod._send_bytes).called_with(bytearray('HPHP48-P,*\xb0\x00\x00abc\x00'))


    @patch('sys.stdin')
    def test_should_return_false(self, mock_stdin):
        mock_stdin.read = Mock(return_value='xyz')
        xmod._send_bytes = Mock(return_value=False)

        ans = xmod.send_file('STDIN')

        sert(ans).is_false()


    @patch('__builtin__.open')
    def test_should_read_from_file(self, mock_open):
        filedata = 'xyz'
        mock_open.return_value.read.return_value = filedata
        xmod._send_bytes = Mock()
        filename = 'abc.txt'
        sert(mock_open).not_called()

        xmod.send_file(filename)

        sert(mock_open).called_with(filename, 'rb')
        sert(mock_open, 'read').called_once()
        sert(mock_open, 'close').called_once()
        sert(xmod._send_bytes).called_with(bytearray(filedata))



class TestRcvResp(Base):

    def test_should_call_rcv_buf(self):
        xmod._rcv_buf = Mock(return_value=(1, None))
        sert(xmod._rcv_buf).not_called()
        sert(xmod.config['ignorerx'].value).is_false()

        ans = xmod._rcv_resp()

        sert(ans).to_equal(1)
        sert(xmod._rcv_buf).called_once()


    @patch('time.sleep')
    def test_should_ack_when_ignorerx_is_true(self, mock_sleep):
        secs = 0.7
        xmod.config['ignore-sec'].value = secs
        xmod.config['ignorerx'].value = True

        ans = xmod._rcv_resp()

        sert(ans).to_equal(R_ACK)
        sert(mock_sleep).called_once_with(secs)



class TestRcvBuf(Base):

    @patch('time.sleep', new=fake_sleep)
    def test_should_return_fail_after_retries(self):
        retries = 30
        tport.peek.return_value = []

        (res, blk) = xmod._rcv_buf()

        sert(res).to_equal(R_FAIL)
        sert(blk).to_equal(None)
        sert(tport.peek).called_n_times(retries)


    @patch('time.sleep', new=fake_sleep)
    def test_should_return_end_trans(self):
        val = [END_TRANS]
        tport.peek.return_value = val
        tport.read_byte.return_value = val

        (res, blk) = xmod._rcv_buf()

        sert(res).to_equal(R_END_TRANS)
        sert(blk).to_equal(None)
        sert(tport.peek).called_once()
        sert(tport.read_byte).called_once()


    @patch('time.sleep', new=fake_sleep)
    def test_should_return_ack(self):
        val = [ACK]
        tport.peek.return_value = val
        tport.read_byte.return_value = val

        (res, blk) = xmod._rcv_buf()

        sert(res).to_equal(R_ACK)
        sert(blk).to_equal(None)
        sert(tport.peek).called_once()
        sert(tport.read_byte).called_once()


    @patch('time.sleep', new=fake_sleep)
    def test_should_return_nack(self):
        val = [NACK]
        tport.peek.return_value = val
        tport.read_byte.return_value = val

        (res, blk) = xmod._rcv_buf()

        sert(res).to_equal(R_NACK)
        sert(blk).to_equal(None)
        sert(tport.peek).called_once()
        sert(tport.read_byte).called_once()


    @patch('time.sleep', new=fake_sleep)
    def test_should_handle_single_data_byte(self):
        cnt = xmod.config['npoll'].value
        tport.peek.side_effect = [[65]] * cnt
        tport.read_byte.return_value = [65]

        (res, blk) = xmod._rcv_buf()

        sert(res).to_equal(R_FAIL)
        sert(blk).to_equal(None)
        sert(tport.peek).called_n_times(cnt)


    @patch('time.sleep', new=fake_sleep)
    def test_should_return_block(self):
        val = 132 * [65]
        tport.peek.return_value = val
        tport.read_bytes.return_value = val

        (res, blk) = xmod._rcv_buf()

        sert(res).to_equal(R_BLOCK)
        sert(blk).to_equal(val)
        sert(tport.peek).called_once()
        sert(tport.read_bytes).called_once()


    @patch('time.sleep', new=fake_sleep)
    def test_should_return_cancel(self):
        tport.peek.return_value = [CANCEL, CANCEL, CANCEL]

        (res, blk) = xmod._rcv_buf()

        sert(res).to_equal(R_CANCEL)
        sert(blk).to_equal(None)
        sert(tport.peek).called_twice()


    @patch('time.sleep', new=fake_sleep)
    def test_should_return_cancel2(self):
        tport.peek.return_value = [65, 66, 67, CANCEL, CANCEL, CANCEL]

        (res, blk) = xmod._rcv_buf()

        sert(res).to_equal(R_CANCEL)
        sert(blk).to_equal(None)
        sert(tport.peek).called_twice()


    @patch('time.sleep', new=fake_sleep)
    def test_should_ignore_cancel(self):
        val = [ACK]
        tport.peek.side_effect = [[CANCEL, CANCEL, CANCEL], [CANCEL, CANCEL, CANCEL, 65], val]
        tport.read_byte.return_value = val

        (res, blk) = xmod._rcv_buf()

        sert(res).to_equal(R_ACK)
        sert(blk).to_equal(None)
        sert(tport.peek).called_n_times(3)


    @patch('time.sleep', new=fake_sleep)
    def test_should_clear_non_header_bytes_from_beginning_of_buffer(self):
        fake_buf = [[72, 73, 74, HEADER_BYTE], [END_TRANS]]
        fake_reads = [[i] for i in sum(fake_buf, [])]
        retries = 30
        orig = tport.read_byte.side_effect
        tport.peek.side_effect = fake_buf
        tport.read_byte.side_effect = fake_reads

        (res, blk) = xmod._rcv_buf()

        sert(res).to_equal(R_END_TRANS)
        sert(len(tport.read_byte.mock_calls)).to_equal(5)
        tport.read_byte.side_effect = orig



class TestWriteFile(Base):

    @patch('__builtin__.open')
    def test_should_write_file(self, mock_open):
        filename = 'out.bin'
        dat_in = [65, 66, 67]
        dat_out = [65, 66, 67, 0]
        sert(mock_open).not_called()

        xmod._write_file(filename, dat_in)

        sert(mock_open).called_with(filename, 'wb')
        sert(mock_open, 'write').called_once_with(bytearray(dat_out))
        sert(mock_open, 'close').called_once()


    @patch('__builtin__.open')
    def test_should_trim_padding(self, mock_open):
        filename = 'out.bin'
        dat_in = [65, 66, 67, 0, 0, 0, 0]
        dat_out = [65, 66, 67, 0]
        sert(mock_open).not_called()

        xmod._write_file(filename, dat_in)

        sert(mock_open).called_with(filename, 'wb')
        sert(mock_open, 'write').called_with(bytearray(dat_out))


    @patch('__builtin__.open')
    @patch('src.log.e')
    def test_should_handle_ioerror(self, mock_log, mock_open):
        mock_open.side_effect=IOError('bad thing')
        filename = 'out.bin'
        dat_in = [65]

        xmod._write_file(filename, dat_in)

        sert(mock_log).called_once_with('Failed to write file out.bin')



class TestReceiveFile(Base):

    def test_should_send_initial_nack(self):
        filename = 'out.bin'
        xmod._rcv_buf = Mock(return_value=(R_CANCEL, None))
        sert(tport.clear_buffer).not_called()

        xmod.receive_file(filename)

        sert(tport.clear_buffer).called_once()
        sert(tport.write_byte).called_once_with(NACK)


    def test_should_write_file_on_end_trans(self):
        filename = 'out.bin'
        xmod._rcv_buf = Mock(return_value=(R_END_TRANS, None))
        xmod._write_file = Mock()
        sert(xmod._write_file).not_called()

        xmod.receive_file(filename)

        sert(xmod._write_file).called_once_with(filename, [])


    def test_should_ack_end_trans(self):
        filename = 'out.bin'
        xmod._rcv_buf = Mock(return_value=(R_END_TRANS, None))
        sert(tport.write_byte).not_called()

        xmod.receive_file(filename)

        sert(tport.write_byte).called_twice()
        sert(tport.write_byte).first_call_called_with(NACK)
        sert(tport.write_byte).second_call_called_with(ACK)


    def test_should_nack_retries(self):
        retries = xmod.config['send-retry'].value
        filename = 'out.bin'
        xmod._rcv_buf = Mock(return_value=('', None))
        sert(tport.write_byte).not_called()

        xmod.receive_file(filename)

        sert(tport.write_byte).called_n_times(retries+1)
        sert(tport.write_byte).nth_call_called_with(1, NACK)
        sert(tport.write_byte).nth_call_called_with(2, NACK)
        sert(tport.write_byte).nth_call_called_with(3, NACK)
        sert(tport.write_byte).nth_call_called_with(4, NACK)
        sert(tport.write_byte).nth_call_called_with(5, NACK)
        sert(tport.write_byte).nth_call_called_with(6, NACK)


    def test_should_ack_good_block(self):
        filename = 'out.bin'
        block = make_block(1, [65])
        xmod._rcv_buf = Mock(side_effect=[(R_BLOCK, block), (R_END_TRANS, None)])
        sert(tport.write_byte).not_called()
        xmod._write_file = Mock()

        xmod.receive_file(filename)

        sert(tport.write_byte).called_n_times(3)
        sert(tport.write_byte).nth_call_called_with(1, NACK)
        sert(tport.write_byte).nth_call_called_with(2, ACK)
        sert(tport.write_byte).nth_call_called_with(3, ACK)


    def test_should_write_blocks(self):
        filename = 'out.bin'
        pkt1 = 128 * [65]
        pkt2 = 128 * [66]
        block1 = make_block(1, pkt1)
        block2 = make_block(2, pkt2)
        xmod._rcv_buf = Mock(side_effect=[(R_BLOCK, block1), (R_BLOCK, block2), (R_END_TRANS, None)])
        xmod._write_file = Mock()
        sert(xmod._write_file).not_called()

        xmod.receive_file(filename)

        sert(xmod._write_file).called_once_with(filename, pkt1 + pkt2)



class TestHelp(Base):

    @patch('src.util.show_help')
    def test_should_call_help(self, mock_util):
        xmod.help('abc')

        sert(mock_util).called_once()
        rgs = mock_util.call_args.args
        sert(len(rgs)).to_equal(5)
        sert(      is_log(rgs[0])).is_true()
        sert(             rgs[1]).to_equal('abc')
        sert(     is_cmds(rgs[2])).is_true()
        sert(   is_config(rgs[3])).is_true()
        sert(is_const_dct(rgs[4])).is_true()



class TestShowConfig(Base):

    @patch('src.util.show_config')
    def test_should_call_show_config(self, mock_util):
        xmod.show_config('abc')

        sert(mock_util).called_once()
        rgs = mock_util.call_args.args
        sert(len(rgs)).to_equal(4)
        sert(   is_config(rgs[0])).is_true()
        sert(is_const_dct(rgs[1])).is_true()
        sert(      is_log(rgs[2])).is_true()
        sert(             rgs[3]).to_equal('abc')



class TestSetConfig(Base):

    @patch('src.util.set_config')
    def test_should_call_set_config(self, mock_util):
        xmod.set_config('abc def')

        sert(mock_util).called_once()
        rgs = mock_util.call_args.args
        sert(             rgs[0]).to_equal('abc def')
        sert(   is_config(rgs[1])).is_true()
        sert(is_const_dct(rgs[2])).is_true()
        sert(      is_log(rgs[3])).is_true()
