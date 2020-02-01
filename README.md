# HpirComm

HpirComm is a Python 2.7 program that can communicate with an HP48G calculator through its IR port by using the computer's sound card as a modem. The Kermit, XMODEM or serial protocol can be used for communication. A simple hardware device must be constructed.

HpirComm supports '[quarter-duplex](./progs/quarter-duplex.md)' mode. Normally, HpirComm and HP48G operate in half-duplex mode, which requires both a receiver and a transmitter. If _only_ a receiver, or _only_ a transmitter is available, HpirComm can still send and receive files.

The only external modules that are used are [`PyAudio`](https://pypi.org/project/PyAudio/) for cross-platform audio control, and (optionally) [`coverage`](https://pypi.org/project/coverage/) for tests.

HpirComm has only been tested with an HP48G on Linux, but should also work on Linux, Windows, or macOS with HP48S, HP48SX, or HP48GX. The software will not work with an HP50G because it uses a different IR protocol (IrDA).

HpirComm is released under [GPL version 2](https://www.gnu.org/licenses/old-licenses/gpl-2.0.txt)

# Short Version

1. Cut a male-to-male 3.5mm audio cord (mono or stereo) in half.
1. Connect one half to an IR emitter; the other half to an IR photodiode.

          _                                 _
         ( )_______________                ( )_______________
         |_|             __|_              |_|             __|__
         |_|             \  /              |_|              /\
         | |______      __\/__             | |______       /__\
        _|_|_     |        |              _|_|_     |        |
       |     |    |________|             |     |    |________|
       |     |                           |     |
       |     |       IR emitter          |     |         IR photodiode
       \     /                           \     /
        \___/                             \___/
         ||                                ||
         ||                                ||

       TRANSMITTER                       RECEIVER

1. Plug the Transmitter into the headphone port and the Receiver into the microphone port.
1. Align Transmitter and Receiver with HP48G.

                                  _______________________
                                  |        COMPUTER    
                                  |                      
                                  |                      
           _______________________| Headphone port       
          |      Transmitter      |                      
          |  _____________________|                      
          | |      Receiver       | Microphone port      
          U U                     |                      
        ____________              |______________________
       |   ^        |
       |  HP48G     |
       |            |

1. Start the Kermit server on the HP48G.  
      `[L-Shift]` `[R-Arrow]`
1. Send a file to the HP48G.  
      `python hpir.py --send ./progs/PAS48`
1. Get a file from the HP48G.  
      `python hpir.py --get PAS48`



# Long Version

* [Hardware](./docs/hardware.md)
* [Calibration](./docs/calibrate.md)
* [Software](./docs/software.md)
* [HP Programs](./progs/progs.md)


# Programs

   Name       |  Description
--------------|--------------
hpir.py       | The HpirComm program
run_tests.py  | Run Unit Tests
cov.py        | Run Unit Tests and generate Coverage report
decode_wav.py | Utility program
clean.sh      | Removes auto-generated files
