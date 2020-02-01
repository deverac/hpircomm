# Quarter-duplex mode

Quarter-duplex mode should be used only as a last resort. It is not recommended.

When communicating via IR, the HP48G normally operates in half-duplex mode. Half-duplex mode requires both a transmitter and a receiver.

If materials are limited, and only a transmitter can be constructed, it is still possible to send data to, and receive data from, the HP48G.

In quarter-duplex mode, there is no way for the remote machine to signal that the received data was corrupt. The sender can only send data and hope that it is received without error. As such, the more data that is transmitted, the more likely there is to be some sort of data corruption.


## Sending data from computer to HP48G

Normally, quarter-duplex will not work with Kermit or XMODEM because both protocols require responses from the remote client when sending data. HpirComm can pretend to receive valid responses while 'blindly' sending data. Provided the sent data is not corrupted during transmission, the file transfer will succeed.

Open the IR port on the HP48G before transmitting to it. (`[L-Shift]` `[I/O]` `[NXT]` `|SERIAL|` `|OPENIO|`)

If the data to be sent is more that 255 bytes, do not use the serial protocol. The serial buffer of the HP48G can hold a maximum of 255 bytes; anything over that is ignored.

Below, `H:` means the HP48G, `C:` means the computer.

#### XMODEM
1. C: Plug device into headphone port.
1. C: `python hpir.py`
1. C: `xmodem set ignorerx True`
1. H: `'PAS48'`     # Put name to hold data on stack
1. H: `[L-Shift]` `[I/O]` `[NXT]` `|XRECV|`
1. C: `xmodem send ./progs/PAS48`

Alternatively, set `ignorerx` in `hpir.ini` and run `python hpir.py --xmodem --send ./progs/PAS48`.

#### Kermit
1. C: Plug device into headphone port.
1. C: `python hpir.py`
1. C: `kermit set ignorerx True`
1. H: `[L-Shift]` `[I/O]` `|RECV|`
1. C: `kermit send ./progs/PAS48`

Alternatively, set `ignorerx` in `hpir.ini` and run `python hpir.py --send ./progs/PAS48`.

#### Serial

1. C: Plug device into headphone port.
1. C: `python hpir.py`
1. C: `serial send file ./progs/PAS48`
1. H: `[L-Shift]` `[I/O]` `[NXT]` `|SERIAL|` `|BUFLEN|` `[DROP]` `|SRECV|`    
1. H: `<< "12" SWAP + # 402Bh SYSEVAL # 62B9Ch SYSEVAL >>` `[EVAL]`
1. H: `'PAS48'` `[STO]`

Step 4 will leave a string starting with 'HPHP48...' on the stack. Step 5 will convert that string to a binary object. FIXIT or OBJFIX perform the same function and may give better results. Use as desired.

Alternatively, run `python hpir.py --serial --send ./progs/PAS48`.

## Sending data from HP48G to computer

Sending data from the HP48G to the computer is accomplished by re-purposing the transmitter to act as the receiver. Be sure to [calibrate the receiver](./calibrate.md) before use.

In quarter-duplex mode, the Kermit and XMODEM protocols are incapable of sending data from the HP48G; the serial protocol must be used. The ASCMIT program is used to encode and then transmit the encoded data. ASCMIT can be found in the ./progs directory.

1. C: Plug device into microphone port.
1. C: `python hpir.py --serial --receive PAS48.asc --timeout 10`
1. H: `'PAS48'`     # Put name on stack
1. H: `|ASCMIT|`    # Encode and transmit data

The data received by the computer (PAS48.asc) will have been encoded by `->ASC`. If the encoded data is sent back to the HP48G, it must be decoded by `ASC->` before use.
