# HpirComm

When HpirComm is started, the HpirComm prompt is shown.

    $ python hpir.py
    Reading init script hpir.ini
    >

Commands can be entered at the prompt.

    > echo Hello World
    Hello World
    > set exit-on-error true
      exit-on-error: true

There are three protocols: `kermit`, `serial`, `xmodem`. Each has its own, independent, commands and config values which can be accessed by prefixing a  command with the protocol name.

    > kermit set warning off
      warning: off
    > serial send chars test123
    Sending chars: test123
    > xmodem show pause
      pause: 0.1

When entering commands, it is only necessary to type enough of the command to disambiguate it. However, when setting a config value, the complete value must be supplied. These two commands do exactly the same thing:

    > kermit set warning off
      warning: off
    > k set w off
      warning: off

If a command is ambiguous, an error will be printed.

    > k se w off
    ERROR: Multiple matches for "se". Matches: ['send', 'server', 'set']

Previously entered commands are saved and can be accessed by using the up and down arrow keys.

When showing config values, all matching values will be shown; 'matching' means 'starts with'.

    > kermit show o
      order-by: dsn
      oslope  : desc
    > kermit show se pad
      send:
          padchar: @
          padding: 0

Instead of having to prefix every command with the protocol, the protocol can be set once and any future commands will use that protocol.

    > kermit
    kermit> set warning off
      warning: off
    kermit> quit
    >

If the HP48G's Kermit server is running, typing `kermit remote host` (or equivalent) enters `hpcalc>` mode, which is an interactive mode. In this mode, values are sent to the HP48G, evaluated by the calculator and then its display is returned. To exit `hpcalc>` mode, press `Ctrl-C`.

    > kermit remote host
    Press Ctrl-C to quit
    hpcalc> 6 45 SIN 5 * +
    1:         9.53553390594
    hpcalc> 4 9.8 /
    2:         9.53553390594
    1:         .408163265306
    hpcalc> DROP "ABC"
    2:         9.53553390594
    1:                 "ABC"
    hpcalc>                   (Ctrl-C typed)
    >

In `hpcalc>` mode, the maximum display width of the stack is 80 characters; longer lines are truncated, but are stored correctly on the calculator.


## Hpir commands

Command |  Description
--------|--------------
`echo` [TEXT]          | Echo text.
`help` [TEXT]          | Show this help. Show commands and config names matching TEXT, if supplied.
`kermit` [K-CMD]       | Use Kermit protocol. Execute K-CMD, if supplied.
`listen` [COUNT [SECS]]| For debugging. Listen for incoming data. Listen COUNT times pausing SECS seconds between each. (Default: 30 1)
`peek`                 | For debugging. Peek at data in receive buffer.
`quit`                 | Quit program.
`script` FILE          | Read and execute HpirComm commands from file.
`serial` [S-CMD]       | Use serial protocol. Execute S-CMD, if supplied.
`set` NAME VAL         | Set config value.
`show` [NAME]          | Show config value. Show matching NAMEs, if supplied.
`wait` [SECS]          | Pause for SECS seconds. (Default: 10)
`xmodem` [X-CMD]       | Use Xmodem protocol. Execute X-CMD, if supplied.


# Hpir config values

    exit-on-error : Exit on error {false, true}
    local-echo    : Echo command line locally {false, true}
    log-level     : Set log level {1, 2, 3, 4, 5, 6}
    trace-on-error: Print stack trace on error {false, true}
    wav-prefix    : Set wav prefix

`wav-prefix` is normally not set. When set, two `.wav` files will be opened. One file will record all audio data sent to the sound card. The other file will record all audio data received from the sound card. The filenames of both files will start with the value of `wav-prefix`. Setting `wav-prefix` to `None` will close both files; setting the value to something else will close both files and open two new `.wav` files using the new prefix.

Any config values that are set during a session are reverted when the program exits. To 'persist' config values, set the config values in the init file (`hpir.ini`).

The history file, which records entered commands, will not be updated if `exit-on-error` is `true` and an exception occurs.

## Serial commands

Command |  Description
--------|--------------
`help` [TEXT]     | Show this help. Show commands and config names matching TEXT, if supplied.
`quit`            | Quit serial mode.
`receive` FILE    | Receive data and save it to filename. The `mode` config value determines the receive method.
`send chars` TEXT | Send text.
`send file` FILE  | Send contents of file.
`set` NAME VAL    | Set config name.
`show` [NAME]     | Show config values. Show matching NAMEs, if supplied.

The calculator's serial buffer can hold a maximum of 255 bytes. All data past 255 bytes will be ignored by the calculator. If the `log-level` is set to `3`, or higher, a warning will be printed when sending more than 255 bytes.

## Serial config

    mode    : Receive mode {timeout, watchars}
    parity  : Parity {even, mark, none, odd, space}
    timeout : Receive data until given time has elapsed
    watchars: Receive data until given chars are received

`mode` determines how the program will behave when receiving a file. When `mode` is set to `timeout`, the program will listen for the period of time specified by the `timeout` value and then save all data that was received during that time. When `mode` is set to `watchars`, the program inspects the incoming data looking for the string specified by the `watchars` value. Once the string has been received, all data that was received prior to it is saved. The string, itself, is not saved. Be aware that if the watchar string is corrupted during transmission, the corrupted data will be stored and the program will continue waiting.

`parity` sets the parity to use for communication. This must match the parity setting on the HP48G. When using '[quarter-duplex](./quarter-duplex.md)' mode, setting parity is advised.


## XMODEM commands

Command |  Description
--------|--------------
`help` [TEXT]  | Show this help. Show commands and config names matching TEXT, if supplied.
`quit`         | Quit xmodem protocol.
`receive` FILE | Receive data and save as filename.
`send` FILE    | Send contents of filename.
`set` NAME VAL | Set config name.
`show` [NAME]  | Show config values. Show matching NAMEs, if supplied.


## XMODEM config

    cpause       : Seconds to wait when double-checking cancel
    ignore-sec   : Seconds to pause between packets
    ignorerx     : Ignore response
    init-wait    : Number of receive-loops to wait to send file
    npoll        : Number of receive-loops before timeout
    pad-char     : Pad character
    pause        : Seconds between receive-loops
    receive-retry: Number of retries when an invalid packet is received
    send-retry   : Number of retries when a sent packet is rejected

See the 'Kermit config' section for `ignore-sec` and `ignorerx`. All other config values for XMODEM should not need to be changed and are for debugging and experimenting.

## Kermit commands

Command |  Description
--------|--------------
`echo` [TEXT] | Echo text
`finish`      | Send Kermit Finish packet to HP48G
`get` FILE    | Get file from HP48G
`help`        | Show this help
`local cwd` [DIR]  | Change working directory
`local delete` FILE| Delete file
`local directory`  | Display directory listing
`local path`       | Display the current path
`local push`       | Start local command interpreter
`local run` CMD    | Run command
`local space`      | Show free and used space on disk
`local type` FILE  | Display the contents of file
`quit`        | Quit kermit protocol
`receive`     | Receive file
`remote cwd` [DIR]  | Change working directory
`remote delete` FILE| Delete file
`remote directory`  | Display directory listing
`remote host` [CMD] | Run command
`remote path`       | Display current path
`remote space`      | Show free space
`remote type` FILE  | Display the contents of file
`send` FILE   | Send file
`server` [DIR]| Change to DIR and start a Kermit server
`set` NAME VAL| Set config value
`show` [NAME] | Show config values
`take` FILE   | Read and execute Kermit commands from file


`local directory` Uses the `order-by` and `oslope` config values to control its output.

`local push` See the Kermit config value `shell` for more info.

`local space` Gives a rough, arguably inaccurate, approximation of disk usage. If exact values are needed, use `local run` to execute an appropriate command.

For all `local` commands (e.g. `local path`), typing `local` is optional.

`remote cwd` If DIR is not specified, `HOME` will be used for DIR. Curly braces will be added to DIR if they are absent. e.g. `remote cwd DIR1` will be converted to `remote cwd { DIR1 }`. Since the HP48G will not allow a directory named 'HOME' to be created, if DIR starts with 'HOME', it is interpreted as an absolute path. e.g. `remote cwd HOME DIR1`.

`remote host` If CMD is not specified, HpirComm will enter the interactive `hpcalc>` mode. Commands entered in `hpcalc>` mode will be sent to the HP48G, evaluated by the HP48G, and the results sent back to the computer.

`server` While in server mode, HpirComm will respond to `|FINISH|`, `|KGET|`, `|PKT|`, `|SEND|` commands that are issued by the HP48G, as described below.

Unless otherwise specified, executing any PKT command will leave an empty string ("") on the stack.

HP48G command | Description
----|-------------
"text" "C" \|PKT\| | Hpircomm prints 'Executing cmd: text' to console. The text will be run as a command and the output of the command will be printed to the console and returned to the HP48G. Any command that your command processor understands should work. e.g. "pwd; ls"
"text" "E" \|PKT\| | Hpircomm prints 'Remote error: text' to console. The HpirComm Kermit server will exit.
"F" "G" \|PKT\| | Hpircomm returns 'Goodbye'. The HpirComm Kermit server will exit.
"I" "G" \|PKT\| | Hpircomm returns "\nHpirComm Server"
"L" "G" \|PKT\| | Same as 'F' 'G'
"M:text" "G" \|PKT\| | Hpircomm prints 'Message: text' to console.
"init-string" "I" \|PKT\| | HpirComm will return the string that it uses when initializing a connection. init-string should be exactly eight characters: __1)__ `Max packet length` (0-94) + 32; __2)__ `Timeout in seconds` (0-94) + 32; __3)__ `Number of pad chars` (0-94) + 32; __4)__ `Pad char` ASCII code + 32; __5)__ `Packet terminator` ASCII code + 32; __6)__ `Control prefix` char; __7)__ `Eighth-bit prefix` char; __8)__ `Blockcheck type (1-3)` char. Executing `{ 126 42 32 64 45 36 78 51 } CHR OBJ-> 2 SWAP << START + NEXT >> EVAL` will generate the init-string: `"~* @-$N3"`. Beware of including '#' in init-string. See the Bugs section for more details.
"init-string" "S" \|PKT\| | Same as "init-string" "I".
"name" "R" \|PKT\| | Retrieves file from computer named "name". HpirComm returns a string composed of the name, followed by a newline character, followed by the contents of the file. To remove the filename and newline from the front of the string, run `<< DUP DUP 10 CHR POS 1 + SWAP SIZE SUB >>`. The file contents will be left on the stack as a string. Use the SPTR, OBJFIX, FIXIT, or similar program to convert the string to a binary object. Using KGET is much easier.
'NAME' \|SEND\| | Send name to computer. (Note the single quotes around NAME.)
"name" \|KGET\| | Fetch name from computer and save.
\|FINISH\| | The HpirComm Kermit server will exit.




## Kermit config

    comment-char: The comment char in script
    debug       : Show sent and received packet data {off, on}
    default-name: Name to use when a valid name cannot be generated
    ignore-sec  : Seconds to pause between packets
    ignorerx    : Ignore response
    order-by    : Sort keys {dn, dsn, n, sdn, sn}
    oslope      : Sort direction {asc, desc}
    receive     :
        bin-prefix     : 8-bit prefixing
        block-check    : Block check {1, 2, 3}
        ctl-prefix     : The control-prefix character
        end-of-line    : End-of-line character
        packet-length  : Packet length
        padchar        : Padding character
        padding        : Number of padding characters
        start-of-packet: Start-of-packet character
        timeout        : Timeout value
    send        :
        bin-prefix     : 8-bit prefixing
        block-check    : Block check {1, 2, 3}
        ctl-prefix     : The control prefix character
        end-of-line    : End-of-line character
        packet-length  : Packet length
        padchar        : Padding character
        padding        : Number of padding characters
        start-of-packet: Start-of-packet character
        timeout        : Timeout value
    shell       : Absolute path to shell executable
    transfer    : Transfer type {binary, text}
    warning     : Warn when overwriting file {off, on}


`default-name` The HP48G does not allow certain names to be used as filenames (e.g. 'PICT'). If the filename to send (e.g. 'pict.txt') results in an illegal name, the value of `default-name` will be used as the filename. If the value of `default-name` is, itself, an invalid name, the transfer will fail.

`ignore-sec` The number of seconds to wait between sending packets. This is only relevant if `ignorerx` is `true`.

`ignorerx` When `true`, this ignores all transmissions from the HP48G and pretends a valid response was received. When using '[quarter-duplex](./quarter-duplex.md)' mode and the Kermit or XMODEM protocol, this must be set to `true`. See also `ignore-sec`.

`order-by` The directory sort keys: d=Date, n=Name, s=Size. `sdn` means sort by Size, then by Date, then by Name.

`oslope` The directory order: `asc`=Ascending, `desc`=Descending.

`send` The Kermit parameters to send to the HP48G. These should not need to be modified.

`receive` The receive parameters are set by the HP48G during initial connection. They cannot be set locally.

`shell` When the `push` command is executed, a command interpreter will be launched. If a different command interpreter is preferred, specify its full path as the value for `shell`. Technically, this need not be a command interpreter. Any executable command could be specified.

`transfer` Affects sending, only. If set to `binary`, files will be sent without modification. If set to `text`, all bytes outside the ASCII values, 10 and [32-127], will be stripped from the file before sending.

The HP48G's ROM version is set in every file that it sends. As a result, a file downloaded from the Internet, sent to the HP48G, and then retrieved from the HP48G, may differ from the original file by exactly one byte (the ROM version).  


## Command-line

    $ python hpir.py --help
    usage: hpir.py [-h] [--kermit] [--xmodem] [--serial] [-s FILE] [-r FILE]
                   [--text] [-n NAME] [--get VAR] [-c CHARS] [-t SECS] [-w TEXT]
                   [--wavprefix PREFIX] [--framerate RATE] [--sensitivity FLOAT]
                   [--showinit] [-l] [--init SCRIPT]

    Options

    protocol:
      --kermit             Use Kermit protocol (default)
      --xmodem             Use XMODEM protocol
      --serial             Use Serial port

    file:
      -s, --send FILE      Filename to send (or STDIN)
      -r, --receive FILE   Outfile filename (or STDOUT)

    kermit:
      --text               Only send printable text and LF chars
      -n, --name NAME      Save to NAME when sending a file
      --get VAR            Get VAR from calc

    serial:
      -c, --chars CHARS    Text to send
      -t, --timeout SECS   Receive until time has elapsed
      -w, --watchars TEXT  Receive until text has been received

    config:
      --wavprefix PREFIX   Write WAV files. Filenames will start with prefix
      --framerate RATE     Set framerate of WAV files.
      --sensitivity FLOAT  Rx sensitivity [0.0 - 1.0]
      --showinit           Show PyAudio initialization
      -l, --log            Logging verbosity. See details below.
      --init SCRIPT        Run script on start. Use '--init=' to disable.
                           (default: hpir.ini)

    help:
      -h, --help           show this help message and exit

    The log level is like a volume slider bar for logging. Specifying once turns
    all logging off. Specifying five times is "max volume"; default is five. When
    Kermit and '--receive' are used, FILE is required, but ignored; the filename
    is set by the sender.

HpirComm uses PyAudio to access the soundcard. PyAudio's startup can be visually noisy so its output has been suppressed. `--showinit` will display PyAudio's startup messages, which may help to trouble-shoot audio issues.

All parameters are optional, but not all parameters are compatible with each other. Parameters may be specified in any order. Command-line parameters have the general form:

    python hpir.py [CONFIG] [PROTOCOL] [FILE] [EXTRA]

  Section |  Description
----------|--------------
[CONFIG]  | Is any combination of the options shown in the `config:` section.
[PROTOCOL]| Is one of the options shown in the `protocol:` section. If it is not supplied, `--kermit` will be used. If PROTOCOL is supplied and no other (valid) options are supplied, then the program will start in the corresponding mode. For example, if `--serial` is supplied, then the program will switch to `serial>` mode on startup.
[FILE]    | Is one of the options shown in the `file:` section. In almost all cases this must be supplied; exceptions are if `--get`, or `--chars` is used.
[EXTRA]  | Is any additional options. Valid options depends on previously supplied options. Examples: If `--kermit` was supplied, then `--ascii` could appear here. If `--serial` was supplied, then `--chars` could appear here.


## Command-line examples

__Kermit examples__

`--kermit --send ./progs/PAS48`  
`--kermit --send notes.txt`  
`--kermit --send notes.txt --text`  
`--kermit --send ./progs/PAS48 --name pas`  
`--kermit --get PAS48`  

__Serial examples__

`--serial --chars ABC`  
`--serial --send notes.txt`  
`--serial --receive dat.bin --timeout 20`  
`--serial --receive dat.bin --watchars ZZ`  
`echo abc | python hpir.py --serial --send STDIN`  
`python hpir.py --serial --timeout 20 --receive STDOUT > abc.txt`  

__XMODEM examples__

`--xmodem --receive PAS48`  
`--xmodem --send ./progs/PAS48`  

When sending a file using Kermit, the filename will be capitalized and have its extension removed. The `--name` option will override this behavior.

Using `--text` is equivalent to setting the Kermit config `transfer` to `ascii`.

In general, command-line parameters are converted into equivalent script commands and then executed. For example, `--serial --send notes.txt` will be converted to the script command `serial send file notes.txt`.

Command-line parameters are processed after all init scripts have been processed.

When specifying command-line parameters, a terminating `quit` command will be executed, which will exit the program. The exception to this is if only a protocol is specified (e.g. `--serial`). In those cases the program will start up in the specified mode; no `quit` command will be issued.

Only enough of a command-line parameter needs to be specified to disambiguate it. For example, `--x` could be used instead of `--xmodem`.

Command-line parameters may also be specified in the comments within the init script by prefixing them with the text `args:`. The parameters may appear on a single line or on multiple lines. If on multiple lines, they need not be sequential.

    ;;; Command-line parameters on a single line
    ; args: --send notes.txt --name INFO --sensitivity 0.21 --wavprefix dat


    ;;; Command-line parameters on multiple lines
    ; args: --send notes.txt
    ; args: --name INFO
    ; args: --sensitivity 0.21
    ; args: --wavprefix dat

All command-line parameters, except `--init`, can be included in an init script and will be appended to the actual command-line parameters. Parameters in sub-scripts are ignored.

# Pre-config

Prior to sending or receiving any data:

1. Disable the clock. `<< -40 CF >>` or toggle off with `[L-Shift]` `[MODES]` `|MISC|` `|CLK|`.

1. Set the communication parameters. `IR` and `2400` baud are mandatory (`<< -33 SF 2400 BAUD >>`); `binary` is recommended (`<< -35 SF >>`); parity, checksum, and translateIO can be your preference (`<< 0 PARITY 3 CKSM 3 TRANSIO >>`). To configure via the UI: `[L-Shift]` `[I/O]` `|IOPAR|`.

         _________________________
        |                         |
        |  IR/wire:       IR      |
        |  ASCII/binary:  binary  |
        |  baud:          2400    |
        |  parity:        none 0  |
        |  cksum: 3  translate: 3 |
        |_________________________|

1. Open the IR port. `[L-Shift]` `[I/O]` `[NXT]` `|SERIAL|` `|OPENIO|`

1. (Optional) When done, close the IR port to save power. `[L-Shift]` `[I/O]` `[NXT]` `|CLOSEIO|`

Pressing a key on the HP48G causes an interrupt to occur. The interrupt may interfere with I/O operations. Because of this, do not press any keys on the HP48G while I/O is occurring (unless the intent of the keypress is to abort the transfer).

# Sending and receiving


### Serial

__Send from computer to HP48G__

1. Open HP48G's serial port.
    * `[L-Shift]` `[I/O]`
    * `[NXT]`
    * `|SERIAL|`
    * `|OPENIO|`
1. Send data from computer.
    * `python hpir.py --serial --send notes.txt`
1. Display received data on HP48G.
    * `[L-Shift]` `[I/O]`
    * `[NXT]`
    * `|SERIAL|`
    * `|BUFLEN|`
    * `[DROP]`
    * `|SRECV|`

__Send from HP48G to computer__

1. Receive data on computer.
    * `python hpir.py --serial --receive hello.txt --watchars ZZ`
1. Send data from HP48G.
    * "Hello World!ZZ"
    * `[L-Shift]` `[I/O]`
    * `[NXT]`
    * `|SERIAL|`
    * `|XMIT|`


### XMODEM

The XMODEM protocol specifies that the sender should wait until it receives a packet from the receiver before sending data. So the send operation should be started before the receive operation.

__Send from computer to HP48G__

1. Open HP48G's serial port.
    * `[L-Shift]` `[I/O]`
    * `[NXT]`
    * `|SERIAL|`
    * `|OPENIO|`
1. Send data from computer.
    * `python hpir.py --xmodem --send note.txt`
1. Receive data on HP48G.
    * `'NOTE'`           # Put name to store data on stack
    * `[L-Shift]` `[I/O]`
    * `[NXT]`
    * `|XRECV|`

__Send from HP48G to computer__

1. Send data from HP48G.
    * `'PAS48'`           # Put name to send on stack
    * `[L-Shift]` `[I/O]`
    * `[NXT]`
    * `|XSEND|`
1. Receive data on computer.
    * `python hpir.py --xmodem --receive PAS48`


### Kermit

__Using the HP48G Kermit server__

1. Start the HP48G Kermit server: `[L-Shift]` `[R-Arrow]`
1. Send data to the HP48G: `python hpir.py --send ./progs/PAS48`
1. Get data from the HP48G: `python hpir.py --get PAS48`


__Using the HpirComm Kermit server__

1. Start HpirComm Kermit server.
    * `python hpir.py`
    * `kermit server`
1. Get data from computer.
    * `./progs/PAS48`
    * `[L-Shift]` `[I/O]`
    * `|SRVR|`
    * `|KGET|`
1.  Send data to computer.
    * `'PAS48'`
    * `[L-Shift]` `[I/O]`
    * `|SEND|`


Instead of transfering files by using commands, the HP48G's UI can be used to transfer files. `[R-Shift]` `[I/O]` `Select Transfer...`. Specify the Type and Name. Populate any additional fields as needed and then issue the desired operation (`|SEND|`, `|RECV|`, `|KGET|`, `|XRECV|`, `|XSEND|`). If the HpirComm Kermit server is not being used, the complementary command will need to be executed on the computer. For example, if the HP48G is sending a file using XMODEM, then `python hpir.py --xmodem --receive DATFIL` must be executed on the computer in order to receive the file that is being sent by the HP48G.

# Bugs

* When starting, PyAudio (version 0.2.11-1) will sometimes fail with: `Expression 'paTimedOut' failed in 'src/os/unix/pa_unix_util.c', line: 387` which results in throwing the Python Exception: `IOError: [Errno -9987] Wait timed out`. I cannot reproduce the error. Restarting the program has always resolved the issue.

* The message `ALSA lib pcm.c:8424:(snd_pcm_recover) underrun occurred` is sometimes printed. HpirComm is at fault for this, not ALSA. The problem is automatically corrected by HpirComm so the message can be safely ignored.

* HpirComm is not as reliable as a wired connection. The error recovery is not great. Sometimes one (or both) sides get stuck and the transfer must be aborted and restarted.

* Neither the Kermit nor the XMODEM protocols are 100% to spec, but they work well enough.

* If '--receive' is used on the command line, a value for FILE must be supplied. When using the Kermit protocol, the value can be anything, but is ignored because the filename is specified by the sender.

* When the HP48G executes a PKT command, it first sends an initial packet in order to establish the communication parameters. The HP48G then executes the PKT command and, if necessary, prefix-encodes any packet data. For 'I' packets, the prefix-encoding of data is unexpected and appears to violate the Kermit protocol specification:

    > "The data fields of all packets are subject to prefix encoding, except the S, I, and A packets and their acknowledgements, (sic) which must not be encoded." pg. 15 of kproto.pdf

    What this means in practice is, if you are going to use 'PKT' to send an 'I' packet from the HP48G, do not specify '#' as the control-prefix (QCTL) or the eight-bit prefix (QBIN). The HP48G subjects both fields to prefix-encoding; all other fields are ignored. If the HpirComm Kermit server receives an 'I' packet with prefix-encoded data, it will cause an exception.

* I am sure there are more.
