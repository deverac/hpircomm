#XXX
import time
import threading
import wave
import struct
import pa


MAX_SHORT = ((2**16) / 2) - 1

CHK = 512


def now():
    return time.time()


def pad_silence(start_time, channels, framerate, sample_width):
    time_span = now() - start_time
    samps = int(channels * framerate * sample_width * time_span)
    aligned_samples = samps + (samps % sample_width)
    return aligned_samples * [0]


class Tx:

    bits_per_sec = 2400

    def __init__(self, samp_width, chan, framerate, show_init, wav_file):
        self.pa = pa.get_instance(show_init)

        self.sample_width = samp_width
        self.channels = chan
        self.framerate = framerate

        self.stop_bits = []
        num_stopbits = 2

        self.wavdat = ''
        self.n = 0
        self.stream = None

        self.wav_file = wav_file

        self.record_session = False
        self.session_buffer = []
        if self.wav_file:
            self.record_session = True

        self.started_at = 0

        self.is_started = False
        self.is_done = False

        samp_pulse = 1
        samp_rem = int(round(float(self.framerate) / self.bits_per_sec)) - samp_pulse

        self.zero_bit = (samp_pulse * [MAX_SHORT]) + (samp_rem * [0]) # Output a pulse for '0'
        self.one_bit = (samp_pulse + samp_rem) * [0] # Output nothing for a '1'

        self.lead = self.one_bit
        self.start_bit = self.zero_bit # Output a zero (pulse) to start
        for _ in range(num_stopbits):
            self.stop_bits += self.one_bit # A stop_bit == a one_bit


    def _callback(self, in_data, frame_count, time_info, status):
        dd = self.sample_width * frame_count
        beg = self.n * dd
        end = beg + dd
        data = self.wavdat[beg:end]

        if self.record_session:
            if self.started_at:
                self.session_buffer.extend(pad_silence(self.started_at, self.channels, self.framerate, self.sample_width))
                self.started_at = 0
            self.session_buffer.extend(data)

        self.n += 1
        if len(data) == 0:
            self.started_at = now()
            return (data, pa.paComplete)
        return (data, pa.paContinue)


    def _start_tx(self):
        if self.is_started:
            return

        self.stream = self.pa.open(format=self.pa.get_format_from_width(self.sample_width),
                        channels=self.channels,
                        rate=self.framerate,
                        stream_callback=self._callback,
                        frames_per_buffer=CHK,
                        output=True,
                        )

        # We need to start and stop the stream for the first transfer to succeed.
        self.stream.start_stream()
        self.stream.stop_stream()

        if self.wav_file:
            self.started_at = now()
        self.is_started = True


    def write_bytes(self, bytes):
        if self.is_done:
            return
        bb = self._encode_bytes(bytes)
        diff = (CHK - (len(bb) % CHK))
        bb.extend(diff * [0])
        bb.extend(2048 * [0]) # 2048 is arbitrary.
        self.wavdat = struct.pack('<'+str(len(bb))+'h', *bb)
        self.n = 0

        self.stream.start_stream()
        while self.stream.is_active():
           time.sleep(0.1)
        self.stream.stop_stream()


    def _encode_bit(self, bit):
        if bit == 1:
            return self.one_bit
        return self.zero_bit


    def _encode_byte(self, byte):
        buf = []
        buf.extend(self.lead)
        buf.extend(self.start_bit)
        for _ in range(8):
            buf.extend(self._encode_bit(byte & 0x01))
            byte >>= 1
        buf.extend(self.stop_bits)
        return buf


    def _encode_bytes(self, bytes):
        buf = []
        for byte in bytes:
            buf.extend(self._encode_byte(byte))
        return buf


    def all_done(self):
        if self.is_done or not self.is_started:
            return
        self.is_done = True
        self.stream.close()
        if self.wav_file:
            self.write_wav(self.wav_file, bytearray(self.session_buffer))


    def set_wav_filename(self, filename):
        if self.wav_file:
            self.write_wav(self.wav_file, bytearray(self.session_buffer))
        self.wav_file = filename
        self.record_session = self.wav_file is not None
        self.session_buffer = []


    # A thread is not needed for Tx, but we mimic the Rx interface.
    def run(self):
        self._start_tx()


    def write_wav(self, filename, dat):
        wf = wave.open(filename, 'wb')
        wf.setparams((self.channels, self.sample_width, self.framerate, 0, 'NONE', 'not compressed'))
        wf.writeframes(dat)
        wf.close()
