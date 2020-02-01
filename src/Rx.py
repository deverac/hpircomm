# XXX
import time
import threading
import wave
import struct
import pa

MAX_SHORT = ((2**16) / 2) - 1

TRIGGER_VAL = int(MAX_SHORT * 0.75) # Arbitrary

# We can't toggle disable and enable listening quickly enough to hear the
# calc's reply, so we have to listen all the time.

class Rx:

    # Spec says min-2340 and max=2460 bit/s.
    bits_per_sec = 2400

    def __init__(self, samp_width, chan, framerate, show_init, wav_file, sensitivity):
        self.pa = pa.get_instance(show_init)
        self.thread = None

        self.sample_width = samp_width
        self.channels = chan
        self.framerate = framerate

        self.sensitivity = sensitivity

        self.samples_per_bit = int(self.framerate / self.bits_per_sec)
        # 10 == 1 start-bit, 8 data-bits, 1 stop-bits
        # Calc sends two stop bits, but we assume only one
        self.samples_per_frame = 10 * self.samples_per_bit

        self.wav_file = wav_file

        self.record_session = wav_file is not None
        self.session_buffer = []

        self.bufr = []
        self.char_buf = []

        self.is_started = False
        self.is_done = False


    def _to_samples(self, binf, num):
        return struct.unpack('<'+str(self.channels * num)+'h', binf)


    def _filtered(self, buf, thold):
        filt = []
        i = 1
        last = len(buf)
        while i < last:
            val = 0
            diff = buf[i-1] - buf[i]
            if diff > 0 and float(diff) / MAX_SHORT > thold:
                val = TRIGGER_VAL
            filt.append(val)
            i += 1
        return filt


    def _callback(self, in_data, frame_count, time_info, status):
        if self.record_session:
            self.session_buffer.extend(list(in_data))
        self.bufr.extend(self._to_samples(in_data, frame_count))
        fb = self._filtered(self.bufr, self.sensitivity)
        p2 = self._decode_buffer(fb)
        self.bufr = self.bufr[p2:]

        return (in_data, pa.paContinue)


    def _start_rx(self):
        if self.is_started:
            return
        self.stream = self.pa.open(format=self.pa.get_format_from_width(self.sample_width),
                        channels=self.channels,
                        rate=self.framerate,
                        input=True,
                        stream_callback=self._callback)
        self.stream.start_stream()

        while not self.is_done:
            time.sleep(0.1)

        self.stream.stop_stream()
        self.stream.close()
        self.pa.terminate()


    def all_done(self):
        if self.is_done or not self.is_started:
            return
        if self.wav_file:
            self.write_wav(self.wav_file, bytearray(self.session_buffer))
        self.is_done = True
        self.thread.join()


    def set_wav_filename(self, filename):
        if self.wav_file:
            self.write_wav(self.wav_file, bytearray(self.session_buffer))
        self.wav_file = filename
        self.record_session = self.wav_file is not None
        self.session_buffer = []


    def _decode_buffer(self, buf):
        buflen = len(buf)
        i = 0
        while i + self.samples_per_frame < buflen:
            if buf[i] == TRIGGER_VAL:
                self._decode_frame(buf[i: i + self.samples_per_frame])
                i += self.samples_per_frame
            else:
                i += 1
        return i


    def _edge_triggers(self, frame):
        edges = []
        frame_len = len(frame)
        i = 0
        while i < frame_len:
            if frame[i] == TRIGGER_VAL:
                edges.append(i)
                i += int(self.samples_per_bit / 2)
            else:
                i += 1
        return edges


    def _decode_frame(self, frame):
        edges = self._edge_triggers(frame)
        in_ch = 0xff
        for e in edges[1:]: # Skip start-bit
            epos = float(e) / self.samples_per_bit
            if epos < 1.5:
                in_ch = in_ch & ~0x01
                continue
            if epos < 2.5:
                in_ch = in_ch & ~0x02
                continue
            if epos < 3.5:
                in_ch = in_ch & ~0x04
                continue
            if epos < 4.5:
                in_ch = in_ch & ~0x08
                continue
            if epos < 5.5:
                in_ch = in_ch & ~0x10
                continue
            if epos < 6.5:
                in_ch = in_ch & ~0x20
                continue
            if epos < 7.5:
                in_ch = in_ch & ~0x40
                continue
            if epos < 8.5:
                in_ch = in_ch & ~0x80
                continue
            # ignore anything larger
        self.char_buf.append(in_ch)


    def peek_bytes(self, n):
        """Peek at a max of n bytes in buffer"""
        return self.char_buf[0:n]


    def read_bytes(self, n):
        """Read a max of n bytes from buffer"""
        buf = self.char_buf[0:n]
        self.char_buf = self.char_buf[n:]
        return buf


    def run(self):
        if self.is_started:
            return
        self.thread = threading.Thread(target=self._start_rx)
        self.thread.start()
        self.is_started = True


    def write_wav(self, filename, dat):
        wf = wave.open(filename, 'wb')
        wf.setparams((self.channels, self.sample_width, self.framerate, 0, 'NONE', 'not compressed'))
        wf.writeframes(dat)
        wf.close()
