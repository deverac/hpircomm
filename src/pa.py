import pyaudio
import sys
import os

# Getting an instance of PyAudio can generate a lot of warnings from
# ALSA and Jack Server. This module suppresses those (and all) warnings.

paContinue = pyaudio.paContinue

paComplete = pyaudio.paComplete

def get_instance(show_init):
    if not show_init:
        stderr = sys.stderr.fileno()
        devnull = os.open(os.devnull, os.O_WRONLY)
        old_stderr = os.dup(stderr)      # Create 'backup' copy of stderr
        sys.stderr.flush()
        os.dup2(devnull, stderr)         # Replace stderr with devnull
        os.close(devnull)

    pa = pyaudio.PyAudio()

    if not show_init:
        os.dup2(old_stderr, stderr) # Restore stderr from 'backup' copy
        os.close(old_stderr)

    return pa
