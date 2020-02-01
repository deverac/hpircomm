#XXX
import sys
import time
import os
import subprocess
import traceback
from collections import namedtuple

import util
import log
import hpchars
from util import ConfigVal as CV

# Per spec, the max size is 94 bytes.
MAX_PAYLOAD_LEN = 94


C = {
    'block-check': {'1': 1, '2': 2, '3': 3},
    'debug': {'off': 0, 'on': 1},
    'transfer': {'text': 2, 'binary': 1},
    'order-by': { 'dsn': 0, 'sdn': 1, 'dn': 2, 'sn': 3,  'n': 4 },
    'oslope': {'asc': 1, 'desc': -1},
    'warning': {'off': 0, 'on': 1},
}


def ctl(i):
  return i ^ 64


def toChar(i):
    return chr(i + 32)


def unChar(ch):
    return ord(ch) - 32



class P:

    def __init__(self, blockcheck=1):
        self.seq = 0
        self.blockcheck = blockcheck

    def _seq(self):
        """0-63 inclusive"""
        seq = self.seq
        self.seq = (self.seq + 1) % 64
        return seq

    def _construct_packet(self, blockcheck, type, data=None):
        return KermitPacket(blockcheck, type, toChar(self._seq()), data)

    def send_initiate(self, parms=None, bc=1):
        return self._construct_packet(bc or self.blockcheck, 'S', parms)

    def receive_initiate(self, name, bc=1):
        return self._construct_packet(bc or self.blockcheck, 'R', name)

    def initialize(self, parms=None, bc=1):
        return self._construct_packet(bc or self.blockcheck, 'I', parms)

    def file_header(self, name, bc=None):
        return self._construct_packet(bc or self.blockcheck, 'F', name)

    def text_header(self, bc=None):
        return self._construct_packet(bc or self.blockcheck, 'X')

    def error(self, msg, bc=None):
        return self._construct_packet(bc or self.blockcheck, 'E', msg)

    def data(self, data, bc=None):
        return self._construct_packet(bc or self.blockcheck, 'D', data)

    def remote_host(self, cmd, bc=None):
        return self._construct_packet(bc or self.blockcheck, 'C', cmd)

    def end_of_file(self, bc=None):
        return self._construct_packet(bc or self.blockcheck, 'Z')

    def end_of_trans(self, bc=None):
        return self._construct_packet(bc or self.blockcheck, 'B')

    def finish(self, bc=None):
        return self._construct_packet(bc or self.blockcheck, 'G', 'F')

    def ack(self, pkt, params=None):
        a_pkt = self._construct_packet(pkt.blockcheck, 'Y', params)
        a_pkt.seq_ch = pkt.seq_ch
        return a_pkt

    def nack(self, pkt):
        n_pkt = self._construct_packet(pkt.blockcheck, 'N')
        n_pkt.seq_ch = pkt.seq_ch
        return n_pkt



class KermitPacket:

    def __init__(self, blockcheck, type, seq_ch, payload, header=0x01):
        self.header = header
        self.blockcheck = blockcheck
        self.type = type # Char
        self.seq_ch = seq_ch
        self.payload = payload

    def length(self):
        if self.blockcheck == 1:
            return self._length1()
        elif self.blockcheck == 2:
            return self._length2()
        elif self.blockcheck == 3:
            return self._length3()
        raise Exception('Invalid length blockcheck {}'.format(self.blockcheck))

    def _length1(self):
        """Returns char value"""
        extra = 3 # seqnum, type, 1-byte checksum
        payload_len = 0
        if self.payload:
            payload_len = len(self.payload)
        return toChar(payload_len + extra)

    def _length2(self):
        """Returns char value"""
        extra = 4 # seqnum, type, 2-byte checksum
        payload_len = 0
        if self.payload:
            payload_len = len(self.payload)
        return toChar(payload_len + extra)

    def _length3(self):
        """Returns char value"""
        extra = 5 # seqnum, type, 3-byte checksum
        payload_len = 0
        if self.payload:
            payload_len = len(self.payload)
        return toChar(payload_len + extra)

    def checksum(self):
        if self.blockcheck == 1:
            return self._checksum1()
        elif self.blockcheck == 2:
            return self._checksum2()
        elif self.blockcheck == 3:
            return self._checksum3()
        else:
            raise Exception('Invalid checksum blockcheck {}'.format(self.blockcheck))

    def _checksum1(self):
        total = 0
        total += ord(self.length())
        total += ord(self.seq_ch)
        total += ord(self.type)
        if self.payload:
            total += sum([ord(p) for p in self.payload])
        return toChar((total + ((total & 192)/64)) & 63)

    def _checksum2(self):
        total = 0
        total += ord(self.length())
        total += ord(self.seq_ch)
        total += ord(self.type)
        if self.payload:
            total += sum([ord(p) for p in self.payload])
        b1 = toChar(total & 0x3F)
        b2 = toChar((total >> 6) & 0x3F)
        return [b2, b1]

    def _checksum3(self):
        ary = []
        ary.append(self.length())
        ary.append(self.seq_ch)
        ary.append(self.type)
        if self.payload:
            ary.extend(self.payload)

        crc = 0 # Start CRC off at 0
        i = 0
        pl = len(ary)
        while pl > 0: # FIXME Make loop, not decrement
            c = ord(ary[i]) #<byte at position i> # Get current byte
            #if parity:
            #    c = c & 127; # Mask off any parity bit
            q = (crc ^ c) & 15 # Do low-order 4 bits
            crc = (crc / 16) ^ (q * 4225)
            q = (crc ^ (c / 16)) & 15 # And high 4 bits
            crc = (crc / 16) ^ (q * 4225)
            i += 1 # Position of next byte
            pl -= 1 # Decrement packet length
        b1 = toChar(crc & 0x3F)
        b2 = toChar((crc >> 6) & 0x3F)
        b3 = toChar((crc >> 12) & 0x0F)
        return [b3, b2, b1]

    def to_list(self):
        """Encode a KermitPacket as a list of chars"""
        buf = []
        buf.append(chr(self.header))
        buf.append(self.length())
        buf.append(self.seq_ch)
        buf.append(self.type)
        if self.payload:
            buf.extend(self.payload)
        buf.extend(self.checksum())
        buf.extend('\r')
        return buf

    def __str__(self):
        if not self.type:
            return '(nullPacket)'
        return ' '.join(self.to_list())



class KermitProtocol:

    def __init__(self, transport):
        self.transport = transport
        # The `send` and `receive` parameters correspond to the following
        # fields in the Kermit protocol specification (pg. 19):
        # packet-length=MAXL, timeout=TIME, padding=NPAD, padchar=PADC,
        # end-of-line=EOL, ctl-prefix=QCTL, block-check=CHKT, bin-prefix=QBIN.
        self.config = {
            'order-by':     CV(C['order-by']['dsn'], int, 'Sort keys'),
            'oslope':       CV(C['oslope']['desc'], int, 'Sort direction'),
            'comment-char': CV(';', chr, 'The comment char in script'),
            'debug':        CV(C['debug']['off'], int, 'Show sent and received packet data'),
            'default-name': CV('KDAT', str, 'Name to use when a valid name cannot be generated'), # Non-kermit
            'transfer':     CV(C['transfer']['binary'], int, 'Transfer type'),
            'ignorerx':     CV(False, bool, 'Ignore response'),
            'ignore-sec':   CV(0.5, float, 'Seconds to pause between packets'),
            'receive': {
                'end-of-line':     CV(0x0D, int, 'End-of-line character'), # HP sends '\r' as end-of-line.
                'packet-length':   CV(80, int, 'Packet length'),
                #'packet-length':   CV(94, int, 'Packet length'),
                'timeout':         CV(10, int, 'Timeout value'),
                'padding':         CV(0, int, 'Number of padding characters'),
                'padchar':         CV(' ', chr, 'Padding character'),
                'ctl-prefix':      CV('#', chr, 'The control-prefix character'),
                'bin-prefix':      CV('N', chr, '8-bit prefixing'),
                'start-of-packet': CV(0x01, int, 'Start-of-packet character'),
                'block-check':     CV(C['block-check']['1'], int, 'Block check'),
            },
            'send': {
                'end-of-line':     CV(0x0D, int, 'End-of-line character'),
                'packet-length':   CV(94, int, 'Packet length'),
                'timeout':         CV(10, int, 'Timeout value'),
                'padding':         CV(0, int, 'Number of padding characters'),
                'padchar':         CV('@', chr, 'Padding character'),
                'ctl-prefix':      CV('#', chr, 'The control prefix character'),
                'bin-prefix':      CV('N', chr, '8-bit prefixing'),
                'start-of-packet': CV(0x01, int, 'Start-of-packet character'),
                'block-check':     CV(C['block-check']['3'], int, 'Block check'),
            },
            'shell':   CV('', str, 'Absolute path to shell executable'),
            'warning': CV(C['warning']['on'], int, 'Warn when overwriting file'),
        }

#p. 19 of kproto.pdf states "The data field of the Send-Init and the ACK to the Send-Init are literal, that is, there is no prefix encoding."
# However when sending an I using PKT, the fields are encoded.

# p. 15 The data fields of all packets are subject to prefix encoding, except the S, I, and A packets and their acknowledgements, which must not be encoded.

    def get_init_params(self):
        snd = self.config['send']
        params = ''
        params += toChar(snd['packet-length'].value)
        params += toChar(snd['timeout'].value)
        params += toChar(snd['padding'].value)
        params += snd['padchar'].value
        params += toChar(snd['end-of-line'].value)
        params += snd['ctl-prefix'].value
        params += snd['bin-prefix'].value
        params += str(snd['block-check'].value)
        return params


    def set_receive_params(self, pkt):
        payload = pkt.payload
        rcv = self.config['receive']
        rcv['packet-length'].value = unChar(payload[0])
        rcv['timeout'].value = unChar(payload[1])
        rcv['padding'].value = unChar(payload[2])
        rcv['padchar'].value = payload[3]
        rcv['end-of-line'].value = unChar(payload[4])
        rcv['ctl-prefix'].value = payload[5]
        rcv['bin-prefix'].value = payload[6]
        rcv['block-check'].value = int(payload[7])


    def get_hp_name(self, file, name, log):
        new_name = 'KDAT'
        if name:
            new_name = name
        elif file:
            sep = '.'
            bname = os.path.basename(file)
            if sep in bname:
                bname = bname[:bname.index(sep)]
            new_name = bname.upper()
        hp_name = util.get_valid_hp_name(new_name, log)
        if not hp_name:
            hp_name = util.get_valid_hp_name(self.config['default-name'].value, log)
        return hp_name or 'KDAT'


    def write_packet(self, pkt):
        if not pkt:
            log.e('No packet to write')
            return False
        lst = pkt.to_list()
        if self.config['debug'].value:
            log.i('Sending {}'.format(lst))
        self.transport.write_bytes(bytearray(lst))
        return True


    def _prep_buffer(self):
        '''Remove bytes until start-of-packet is at head of buffer'''
        rcv_hdr = self.config['receive']['start-of-packet'].value
        while True:
            b = self.transport.peek_byte()
            if len(b) > 0 and b[0] != rcv_hdr:
                x = self.transport.read_byte()
            else:
                return


    def _remote_eval(self, cmd):
        hpcmd = '{} {} {} EVAL'.format(hpchars.HP_LEFT_CHEVRON, cmd, hpchars.HP_RIGHT_CHEVRON)
        self.send_command(hpcmd)


    def _is_transfer_text(self):
        return self.config['transfer'].value == C['transfer']['text']


    def _send_file(self, filename, is_text, as_name=None):
        hp_name = self.get_hp_name(filename, as_name, log)

        f = open(filename, 'r')
        bytes = f.read()
        f.close()

        if is_text:
            bytes = util.filter_text(util.quote(bytes))

        log.i('Sending file {} as {}'.format(filename, hp_name))
        self._send_bytes(hp_name, bytes)


    def _send_files(self, files, is_text):
        num_files = len(files)
        if num_files == 0:
            raise Exception('No files to send')
        for i, file in enumerate(files):
            if num_files > 1:
                log.i('Sending file {} of {}'.format(i+1, num_files))
            self._send_file(file, is_text, None)


    def _ready_bytes(self):
        '''
            Inspect the buffer for a complete packet. If found, return the number
            of bytes required to read the packet; otherwise return 0.
        '''
        # A Nack is the only packet of length 6; all other packets are larger.
        min_length = 6  # '\x01','#',' ','N','3','\r'    hdr, len, seq, type, chksm, trailer
        extralen = 3 #  hdr, length, trailer
        buf = self.transport.peek()
        buflen = len(buf)
        if buflen >= min_length:
            reclen = unChar(chr(buf[1]))
            packetlen = reclen + extralen
            if buflen >= packetlen:
                return packetlen
        return 0



    def _dislodge_stale_data(self, stale_bytes):
        # We sometimes receive an incomplete/truncated packet or
        # corrupted data (e.g. the length field). This code attempts
        # to 'dislodge' the bad data from the buffer. This code
        # assumes that the sender will stop sending data and listen for
        # a response; if the sender continuously sends data, this code is
        # useless because stale_bytes will never equal peek().
        #if stale_bytes and (stale_bytes == self.transport.peek_bytes()):
        if stale_bytes and (stale_bytes == self.transport.peek()):
            self.transport.read_byte()
            return None
        else:
            return self.transport.peek()


    def _poll_for_packetful_of_bytes(self, max_retries=60, poll_delay=0.1):
        '''
            Wait (max_tries * poll_delay) for a complete packet to appear
            in the buffer. Return the number of bytes required to read the
            packet; return None on timeout.
        '''
        stale_bytes = None
        retries = 0
        self._prep_buffer()
        while retries < max_retries:
            num_bytes = self._ready_bytes()
            if num_bytes:
                bytes = self.transport.read_bytes(num_bytes)
                if self.config['debug'].value:
                    log.i('Received {}'.format([chr(b) for b in bytes]))
                return bytes
            if retries > 1:
                stale_bytes = self._dislodge_stale_data(stale_bytes)
            retries += 1
            time.sleep(poll_delay)
        return None


    def _pstr(self, nm, p):
        if p:
            val = p.to_list()
        else:
            val = None
        return '  {}: {}'.format(nm, val)


    def _choose(self, p1, p2, p3):
        '''
            The same bytes can be decoded to different (valid) Kermit packets
            depending on which blockcheck checksum is used. This method selects
            which of the packets should be used.
        '''
        if (not p2) and (not p3):
            return p1
        elif (not p1) and (not p3):
            return p2
        elif (not p1) and (not p2):
            return p3
        else:
            log.d('Multiple decodes')
            log.d(self._pstr('p1', p1))
            log.d(self._pstr('p2', p2))
            log.d(self._pstr('p3', p3))
            if p1 and p1.type == 'I':
                return p1
            # Prefer the configured block-check.
            bc = self.config['receive']['block-check'].value
            if p1 and bc == 1:
                return p1
            if p2 and bc == 2:
                return p2
            if p3 and bc == 3:
                return p3
            # Prefer more robust blockcheck.
            if p3:
                return p3
            return p2


    def read_any_packet(self, max_retries=60, poll_delay=0.1):
        pkt_bytes = self._poll_for_packetful_of_bytes()
        if pkt_bytes:
            p1 = self.to_packet(pkt_bytes, 1, False)
            p2 = self.to_packet(pkt_bytes, 2, False)
            p3 = self.to_packet(pkt_bytes, 3, False)
            if p1 or p2 or p3:
                return self._choose(p1, p2, p3)
        return None


    def to_packet(self, buf, blockcheck, log_checksum=True):
        """Construct a KermitPacket from buffer"""
        if not buf:
            return None

        if blockcheck == 1:
            min_length = 6 # hdr, len, seq, type, 1-byte chksum, trailer
        elif blockcheck == 2:
            min_length = 7 # hdr, len, seq, type, 2-byte chksum, trailer
        elif blockcheck == 3:
            min_length = 8 # hdr, len, seq, type, 3-byte chksum, trailer
        else:
            log.d('Bad blockcheck value {}'.format(blockcheck))
            return None

        if len(buf) < min_length:
            return None

        header = buf[0]
        length = chr(buf[1])
        seq_ch = chr(buf[2])
        type = chr(buf[3])
        if blockcheck == 1:
            payload = [chr(p) for p in buf[4:-2]]
            chksum = chr(buf[-2])
        elif blockcheck == 2:
            payload = [chr(p) for p in buf[4:-3]]
            chksum = [chr(buf[-3]), chr(buf[-2])]
        else: # blockcheck == 3:
            payload = [chr(p) for p in buf[4:-4]]
            chksum = [chr(buf[-4]), chr(buf[-3]), chr(buf[-2])]
        trailer = buf[-1]

        rcv_header = self.config['receive']['start-of-packet'].value
        if header != rcv_header:
            log.d('Bad header. Expected:{}  Actual:{}'.format(rcv_header, header))
            return None

        if unChar(seq_ch) > 63:
            log.d('Bad seq num. Actual:{} (exceeds 63)'.format(unChar(seq_ch)))
            return None

        if type not in 'BCDEFGINRSXYZ':
            log.d('Unknown type:{}'.format(type))
            return None

        rcv_trailer = self.config['receive']['end-of-line'].value
        if trailer != rcv_trailer:
            log.d('Bad end-of-line. Expected:{}  Actual:{}'.format(rcv_trailer, trailer))
            return None

        pkt = KermitPacket(blockcheck, type, seq_ch, payload, rcv_header)

        if length != pkt.length():
            log.d('Bad length. Expected:{} Actual:{}'.format(length, pkt.length()))
            return None

        if chksum != pkt.checksum():
            if log_checksum:
                log.d('Bad checksum. Expected:{} Actual:{}'.format(chksum, pkt.checksum()))
            return None

        return pkt


    def _write_verify(self, src_pkt, ignore_response=False, max_retries=5):
        """Returns valid packet or None"""
        retries = 0
        while retries < max_retries:
            self.write_packet(src_pkt)
            if ignore_response:
                return None
            pkt = self.read_any_packet()
            if pkt:
                if pkt.type == 'N':
                    log.d('Retrying')
                elif (pkt.type == 'E') or (pkt.seq_ch == src_pkt.seq_ch):
                    return pkt
            retries += 1
        return None



    def _is_resend(self, prev_pkt, pkt):
        return prev_pkt and (prev_pkt.seq_ch == pkt.seq_ch) and (prev_pkt.type == pkt.type)


    def _is_next_seq(self, prev_pkt, pkt):
        '''
            Returns True if the sequence number of pkt succeeds the sequence
            number of prev_pkt; otherwise returns False.
        '''
        # Ideally, this would also enforce the 'type' transitions from prev_pkt
        # to pkt, but the complete type transitions that the HP Calc can send is
        # not known; a message is logged when an unexpected type transition occurs.

        states = {
            'S': 'FX',
            'F': 'D',
            'D': 'DZ',
            'Z': 'BF',
            'B': 'IS',
            'X': 'D',
        }

        if not prev_pkt:
            if pkt.type not in 'ISGECNR':
                # I Initialize
                # S SendInitiate
                # G General
                # E Error
                # C Command
                # N Nack
                # R Receive
                log.d('Bad type. Expected one of "ISGECNR". Actual:{}'.format(pkt.type))
            return True

        prev_seq_num = unChar(prev_pkt.seq_ch)
        cur_seq_num = unChar(pkt.seq_ch)
        is_ok = ((prev_seq_num + 1) % 64 == cur_seq_num % 64)

        if prev_pkt.type in states.keys():
            expected_types = states[prev_pkt.type] + 'NE'
            if pkt.type not in expected_types:
                log.d('Bad type. Expected:{}  Actual:{}'.format(states[prev_pkt.type] , pkt.type))
        else:
            log.d('Previous pkt type {} not in states {}'.format(prev_pkt.type, states.keys()))
        return is_ok


    def _do_ack(self, pkt):
        if pkt.type == 'I' or pkt.type == 'S':
            if unChar(pkt.seq_ch) != 0:
                log.d('Bad initial seq. Expected:0 Actual:{}'.format(unChar(pkt.seq_ch)))
            self.set_receive_params(pkt)
            ack_pkt = P().ack(pkt, self.get_init_params())
        elif pkt.type == 'G' and (pkt.payload == ['F'] or pkt.payload == ['L']):
            ack_pkt = P().ack(pkt, 'Goodbye')
        else:
            ack_pkt = P().ack(pkt)
        self.write_packet(ack_pkt)


    def _do_nack(self, pkt):
        self.write_packet(P().nack(pkt))


    def _is_init_pkt(self, pkt):
        return pkt.type == 'I'


    def _finish(self):
        self.write_packet(P().finish())


    def _get(self, name):
        self._send_then_receive(P().receive_initiate(name))


    def _save_buf_data(self, name, data):
        if name:
            saved_name = name
            i = 0
            while True:
                if not os.path.isfile(saved_name):
                    break
                i += 1
                saved_name = name + '.' + str(i)
            fil = open(saved_name, 'wb')
            fil.write(bytearray(data))
            fil.close()
            if self.config['warning'].value and saved_name != name:
                log.i('Wrote {} as {}'.format(name, saved_name))
            else:
                log.i('Wrote {}'.format(saved_name))
        else:
            log.i(''.join(data))


    def _server(self, exit_on_eot=False, init_pkt=None):
        in_name = None
        in_buf = []

        done = False
        prev_pkt = None
        while not done:
            pkt = init_pkt or self.read_any_packet()
            if init_pkt:
                init_pkt = None
            if not pkt:
                log.d('No packet read')
                continue
            if self._is_resend(prev_pkt, pkt) or self._is_init_pkt(pkt):
                self._do_ack(pkt)
                continue

            if not self._is_next_seq(prev_pkt, pkt):
                self._do_nack(pkt)
                continue

            if pkt.type == 'S':
                self.set_receive_params(pkt)
            elif pkt.type == 'N':
                if unChar(pkt.seq_ch) == 0: # e.g. Command was rejected
                    None # Needed only for test branch coverage module.
                    return
                else:
                    None # Needed only for test branch coverage module.
                    continue
            elif pkt.type == 'G':
                payload = ''.join(pkt.payload)
                if payload == 'F':
                    self._do_ack(pkt)
                    done = True
                elif payload == 'L':
                    self._do_ack(pkt)
                    return
                elif payload.startswith('M:'):
                    log.i('Message: {}'.format(''.join(self._unescape_payload(payload[2:]))))
                elif payload == 'I':
                    self._send_bytes(None, 'HpirComm Server')
                    prev_pkt = None
                    continue
            elif pkt.type == 'F':
                in_name = ''.join(self._unescape_payload(pkt.payload))
                if not in_name:
                    self._do_nack(pkt)
                    continue
            elif pkt.type == 'D':
                in_buf.extend(self._unescape_payload(pkt.payload))
            elif pkt.type == 'Z':
                if in_buf:
                    self._save_buf_data(in_name, in_buf)
                    del in_buf[:] # clear buffer, but keep the same reference
            elif pkt.type == 'C':
                cmd = ''.join(pkt.payload)
                log.i('Executing cmd: {}'.format(cmd))
                p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True) # CAUTION: Security hazard.
                stdout, stderr = p.communicate()
                log.i('{}'.format(stdout))
                self._send_bytes(None, stdout)
                prev_pkt = None
                continue
            elif pkt.type == 'R':
                self._send_file(''.join(pkt.payload), False)
                prev_pkt = None
                continue
            elif pkt.type == 'B':
                if exit_on_eot:
                    done = True
            elif pkt.type == 'X':
                pass
            elif pkt.type == 'E':
                log.i('Remote error: {}'.format(''.join(self._unescape_payload(pkt.payload))))
                self._do_ack(pkt)
                return
            else:
                log.d('Unhandled packet:{}'.format(pkt.to_list()))

            self._do_ack(pkt)
            prev_pkt = pkt



    def is_prefix(self, b):
        # "The character to be prefixed is considered a prefix character if its
        # low-order 7 bits corresponds to an active prefix character ... regardless
        # of the setting of its high-order bit." pg 16
        return chr((ord(b) & 0x7F)) == self.config['send']['ctl-prefix'].value


    def _unescape_payload(self, payload):
        buf = []
        pos = 0
        while pos < len(payload):
            byte = payload[pos]
            if byte == self.config['receive']['ctl-prefix'].value:
                pos += 1
                if pos < len(payload):
                    byte2 = payload[pos]
                    n = ord(byte2) & 0x7F
                    if ctl(n) < 32 or ctl(n) == 127:
                        buf.append(chr(ctl(ord(byte2))))
                    else:
                        buf.append(byte2)
                else:
                    log.e('Bad payload length')
            else:
                buf.append(byte)
            pos += 1
        return buf


    def _receive(self, init_pkt=None):
        self._server(True, init_pkt)


    def construct_payloads(self, strbuf, prefix, max_payload_len):
        payloads = []
        payload = []
        for ch in strbuf:
            to_add = []
            n = ord(ch) & 0x7F

            if chr(n) == prefix:
                to_add.append(prefix)
                to_add.append(ch)
            elif n < 32 or n == 127:
                to_add.append(prefix)
                to_add.append(chr(ctl(ord(ch))))
            else:
                to_add.append(ch)

            if len(payload) + len(to_add) > max_payload_len:
                payloads.append(payload)
                payload = []
            payload.extend(to_add)

        if payload:
            payloads.append(payload)
        return payloads


    def send_abort(self):
        self.write_packet(P().error('Abort'))
        self.write_packet(P().error('Abort'))
        self.write_packet(P().error('Abort'))


    def _bytes_to_packets(self, name, bytes):
        cfg = self.config['send']
        bc = cfg['block-check'].value
        pfx = cfg['ctl-prefix'].value
        max_data_len = cfg['packet-length'].value - bc - 2 # 2 for seq, type

        pp = P(bc)

        packets = []
        packets.append(pp.send_initiate(self.get_init_params()))
        if name:
            packets.append(pp.file_header(name))
        else:
            packets.append(pp.text_header(name))
        payloads = self.construct_payloads(bytes, pfx, max_data_len)
        for i, payload in enumerate(payloads):
            packets.append(pp.data(payload))
        packets.append(pp.end_of_file())
        packets.append(pp.end_of_trans())
        return packets


    def _send_packets(self, packets):
        ignore_response = self.config['ignorerx'].value
        ignorerx = self.config['ignore-sec'].value
        send_max_retries = 6 # Arbitrary
        i = 0
        retries = 0
        while i < len(packets):
            if retries > send_max_retries:
                return False
            log.i('Sending packet #{} of {}'.format(i+1, len(packets)))
            pkt = self._write_verify(packets[i], ignore_response)
            if pkt:
                if pkt.type == 'E':
                    return False
                if packets[i].type == 'S':
                    self.set_receive_params(pkt)
                i += 1
                retries = 0
                continue
            elif ignore_response:
                time.sleep(ignorerx)
                i += 1
                continue
            else:
                log.i('Failed to send packet')

            retries += 1
        return True


    def _send_bytes(self, name, bytes):
        try:
            packets = self._bytes_to_packets(name, bytes)
            self._send_packets(packets)
            return True
        except KeyboardInterrupt as ki:
            log.e('Aborting')
            self.send_abort()
            return False


    def send_command(self, cmd):
        self._send_then_receive(P().remote_host(cmd, 1))


    def _send_then_receive(self, pkt, max_retries=5):
        # Difficult because initial write_packet() may not be received
        # correctly and, per Kermit protocol, we do not get an ACK (but might
        # get a NACK).
        #
        # For 'receive_initiate' (R):
        # "...the only two valid responses to a successfully received R packet
        # are an S packet or an E packet. The R packet is not ACK'd."  p. 26
        self.transport.clear_buffer()
        retries = 0
        while retries < max_retries:
            pkt_in = self._write_verify(pkt)
            if pkt_in and pkt_in.type != 'N':
                self._receive(pkt_in)
                return
            retries += 1
        log.e('Failed to send command {}'.format(pkt.payload))
