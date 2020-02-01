#XXX
import log
import sys
import time
import util

from util import ConfigVal as CV
from util import CmdVal as Cmd


# This implements the 128-byte protocol

# Page 27-13 of HP48G User's Guide says:
# "The XMODEM protocol built into the HP 48 doesn't perform any CRC checking."


# 132 bytes == 1056 bits
# 1056 bits / 2400bps = 0.44secs

C = {}

xmodem_cmds = {
    'help':    Cmd('Show help', '[TEXT]'),
    'quit':    Cmd('Quit xmodem protocol'), # Handled by dispatcher.py.
    'receive': Cmd('Receive data and save to file', 'FILE'),
    'send':    Cmd('Send file', 'FILE'),
    'set':     Cmd('Set config value', 'NAME VAL'),
    'show':    Cmd('Show config values', '[NAME]'),
}


XM = util.AttrBag(
    HEADER     = 0x01,
    END_TRANS  = 0x04,
    ACK        = 0x06,
    NACK       = 0x15,
    CANCEL     = 0x18,
    PACKET_LEN = 128,
    BLOCK_LEN  = (128 + 4), # Header Seq, NegSeq, Checksum
)


R = util.AttrBag(
    BLOCK     = 101, # A block was received
    ACK       = 102, # Ack was received
    NACK      = 103, # Nack was received
    CANCEL    = 104, # Cancel was received
    END_TRANS = 105, # EndTrans was received
    FAIL      = 106, # No response was received
)

# Calc sends three CANCEL bytes when ON is pressed
CCC = [XM.CANCEL, XM.CANCEL, XM.CANCEL]
LENCCC = len(CCC)


def now():
    return time.time()



class Xmodem:

    def __init__(self, transport):
        self.transport = transport
        self.config = {
            'cpause':        CV(3.0,   float, 'Seconds to wait when double-checking cancel'),
            'ignore-sec':    CV(0.5,   float, 'Seconds to pause between packets'),
            'ignorerx':      CV(False, bool,  'Ignore response'),
            'init-wait':     CV(10,    int,   'Number of receive-loops to wait to send file'),
            'npoll':         CV(30,    int,   'Number of receive-loops before timeout'),
            'pad-char':      CV(0x00,  int,   'Pad character'), # XMODEM specifies 0x1A; HP uses 0x00
            'pause':         CV(0.1,   float, 'Seconds between receive-loops'),
            'receive-retry': CV(5,     int,   'Number of retries when an invalid packet is received'),
            'send-retry':    CV(5,     int,   'Number of retries when a sent packet is rejected'),
        }


    def _next_seq(self, n):
        """Increment n by one. Sequence runs from 1-255 (inclusive), then wraps."""
        return (n % 255) + 1


    def _checksum(self, pak):
        """Calculate XMODEM checksum of packet"""
        return sum(pak) % 256


    def _split_data(self, dat):
        pkts = []
        for x in range(0, len(dat), XM.PACKET_LEN):
            pkts.append(dat[x:x + XM.PACKET_LEN])
        if len(pkts) > 0:
            last_packet = pkts[-1]
            last_packet += (XM.PACKET_LEN - len(last_packet)) * chr(self.config['pad-char'].value)
            pkts[-1] = last_packet
        return pkts


    def _construct_blocks(self, pkts):
        """Construct XMODEM blocks from packets"""
        blocks = []
        for i, pkt in enumerate(pkts):
            seq = self._next_seq(i)

            block = []
            block.append(XM.HEADER)
            block.append(seq)
            block.append(255-seq)
            block.extend(pkt)
            block.append(self._checksum(pkt))

            blocks.append(block)
        return blocks


    def _extract_packet(self, blk):
        """Extract packet from XMODEM block"""
        return blk[3:XM.PACKET_LEN+3]


    def _is_valid_block(self, blk, seq):
        if len(blk) != XM.BLOCK_LEN:
            return False
        if blk[0] != XM.HEADER:
            return False
        if blk[1] != seq:
            return False
        if blk[2] != (255-seq):
            return False
        if blk[-1] != self._checksum(blk[3:-1]):
            return False
        return True


    def _send_end_trans(self):
        max_retries = self.config['send-retry'].value
        i = 0
        while True:
            if i >= max_retries:
                return False
            self.transport.write_byte(XM.END_TRANS)
            resp = self._rcv_resp()
            if resp == R.ACK:
                return True
            if resp == R.CANCEL:
                return False
            i += 1


    def _send_bytes(self, bytes):
        max_retries = self.config['send-retry'].value
        init_wait = self.config['init-wait'].value
        blks = self._construct_blocks(self._split_data(bytes))
        lenblks = len(blks)

        self.transport.clear_buffer()
        log.i('Waiting to hear from remote')
        retries = 0
        while True:
            if retries >= init_wait:
                return False
            resp = self._rcv_resp()
            if resp == R.NACK or self.config['ignorerx'].value:
                break
            if resp == R.CANCEL:
                return False
            retries += 1

        log.i('Sending {} bytes in {} blocks'.format(len(bytes), lenblks))
        retries = 0
        block_num = 0
        while True:
            if retries == 0:
                log.i('Block {} of {}'.format(block_num+1, lenblks))
            self.transport.write_bytes(blks[block_num])
            resp = self._rcv_resp()
            if resp == R.CANCEL:
                log.i('Remote host aborted transfer')
                break
            elif resp == R.ACK:
                retries = 0
                block_num += 1
                if block_num >= lenblks:
                    return self._send_end_trans()
            else:
                if resp != R.NACK and resp != R.FAIL:
                    log.d('Unhandled case '+str(resp))
                if retries >= max_retries:
                    log.i('Too many retries.')
                    self.transport.write_bytes(CCC)
                    break
                retries += 1
                log.i('Retrying ' + str(retries))
        return False


    def send_file(self, filename):
        log.i('Sending file {}'.format(filename))
        if filename == 'STDIN':
            bytes = bytearray(util.txt_to_hpbin(sys.stdin.read().strip()))
        else:
            f = open(filename, 'rb')
            bytes = bytearray(f.read())
            f.close()
        ans = self._send_bytes(bytes)
        if not ans:
            log.i('Failed to send file {}'.format(filename))
        return ans


    def _rcv_resp(self):
        """Convenience method for when only resp code is needed; buffer is ignored"""
        if self.config['ignorerx'].value:
            time.sleep(self.config['ignore-sec'].value)
            return R.ACK
        return self._rcv_buf()[0]


    def _rcv_buf(self):
        """Returns (R*, buf) tuple. buf may be None."""
        npoll  = self.config['npoll'].value
        pause  = self.config['pause'].value
        cpause = self.config['cpause'].value

        i = 0
        while i < npoll:
            bytes = self.transport.peek()
            bytes_len = len(bytes)
            if bytes[-LENCCC:] == CCC: # Check last three
                time.sleep(cpause)
                if self.transport.peek()[-LENCCC:] == CCC: # Double-check last three
                    return (R.CANCEL, None)
            elif bytes_len == 1:
                byte = self.transport.read_byte()[0]
                if byte == XM.END_TRANS:
                    return (R.END_TRANS, None)
                if byte == XM.ACK:
                    return (R.ACK, None)
                if byte == XM.NACK:
                    return (R.NACK, None)
            elif bytes_len > 0 and bytes_len < XM.BLOCK_LEN:
                while len(bytes) > 0 and bytes[0] != XM.HEADER:
                    bytes = self.transport.read_byte()
            elif bytes_len >= XM.BLOCK_LEN:
                return (R.BLOCK, self.transport.read_bytes(XM.BLOCK_LEN))
            time.sleep(pause)
            i += 1
        return (R.FAIL, None)


    def _write_file(self, filename, bufdat):
        try:
            if len(bufdat) == 0:
                return
            while bufdat[-1] == 0x00: # HP pads with 0x00
                del bufdat[-1]
            bufdat.append(0x00) # HP objects must end with null.
            log.i('Received ' + str(len(bufdat)) + ' bytes')
            log.i('Saving to file ' + filename)
            f = open(filename, 'wb')
            f.write(bytearray(bufdat))
            f.close()
        except IOError as err:
            log.e('Failed to write file ' + filename)
            return False
        return True


    def receive_file(self, filename):
        max_retries = self.config['receive-retry'].value

        # Send NACK to initiate transfer, per XMODEM protocol. This is not
        # 100% to spec; the protocol specifies that the receiver should send
        # (up to nine) NACKs until the sender responds with the data.
        self.transport.clear_buffer()
        self.transport.write_byte(XM.NACK)

        retries = 0
        seq = 1
        filedat = []
        while True:
            (res, buf) = self._rcv_buf()
            if res == R.BLOCK and self._is_valid_block(buf, seq):
                log.i('Received block ' + str(seq))
                filedat.extend(self._extract_packet(buf))
                self.transport.write_byte(XM.ACK)
                seq = self._next_seq(seq)
                retries = 0
            elif res == R.END_TRANS:
                self.transport.write_byte(XM.ACK)
                return self._write_file(filename, filedat)
            elif res == R.CANCEL:
                log.i('Canceled by remote host')
                break
            else: # RESP_FAIL or bad block
                if retries >= max_retries:
                    log.i('Max retries exceeded')
                    break
                self.transport.clear_buffer()
                self.transport.write_byte(XM.NACK)
                retries += 1
        return False


    def help(self, line=''):
        util.show_help(log, line, xmodem_cmds, self.config, C)


    def show_config(self, line=''):
        util.show_config(self.config, C, log, line)


    def set_config(self, line):
        util.set_config(line, self.config, C, log)
