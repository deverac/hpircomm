import collections
import os
import shlex
import time


import kermit
import log
import serial
import transport
import util
import xmodem

from util import CmdVal as Cmd
from util import ConfigVal as CV


default_args = util.AttrBag(
    init        = None,
    showinit    = None,
    wavprefix   = None,
    framerate   = None,
    sensitivity = None,

    xmodem      = None,
    kermit      = None,
    serial      = None,

    text        = None,
    get         = None,
    send        = None,
    receive     = None,
)

DEFAULT_INI_FILE = 'hpir.ini'

PROMPTER = '> '

C = {
    'exit-on-error': {'true': True, 'false': False},
    'trace-on-error': {'true': True, 'false': False},
    'local-echo': {'true': True, 'false': False},
    'log-level': {'1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6},
}


hpcomm_cmds = {
    'kermit':    Cmd('Use Kermit protocol',      '[K-CMD]'),
    'serial':    Cmd('Use Serial protocol',      '[S-CMD]'),
    'xmodem':    Cmd('Use Xmodem protocol',      '[X-CMD]'),
    'echo':      Cmd('Echo text',                '[TEXT]'),
    'help':      Cmd('Show this help',           '[TEXT]'),
    'listen':    Cmd('Listen for incoming data (30 1)', '[COUNT [SECS]]'),
    'peek':      Cmd('Peek at data in receive buffer'),
    'quit':      Cmd('Quit program'),
    'script':    Cmd('Read and execute HpirComm commands from file', 'FILE'),
    'set':       Cmd('Set config value',         'NAME VAL'),
    'show':      Cmd('Show config values',       '[NAME]'),
    'wait':      Cmd('Wait for SECS secs (10)',            '[SECS]'),
}


def read_scripts(line):
    scripts = []
    names = shlex.split(line.strip())
    for name in names:
        cmds = util.read_script(name)
        for cmd in cmds[::-1]:
            scripts.insert(0, cmd)
    return scripts



class SerialCmds:

    def __init__(self, transport):
        self.serial = serial.Serial(transport)


    def _send(self, line):
        cmd, tail = util.parse_cmdline2(line, ['file', 'chars'], log)

        s = self.serial

        if cmd == 'file':
            s.send_file(tail)
        elif cmd == 'chars':
            s.send_chars(tail)
        else:
            log.i('Invalid send: ' + line)


    def exec_line(self, line):
        cmd, tail = util.parse_cmdline2(line, ['send', 'receive', 'help', 'show', 'set'], log)
        s = self.serial

        if cmd == 'send':
            self._send(tail)
        elif cmd == 'receive':
            s.receive_file(tail)
        elif cmd == 'show':
            s.show_config(tail)
        elif cmd == 'set':
            s.set_config(tail)
        elif cmd == 'help':
            s.help(tail)
        else:
            log.i('Invalid {}'.format(line))



class XmodemCmds:

    def __init__(self, transport):
        self.xmodem = xmodem.Xmodem(transport)


    def exec_line(self, line):
        cmd, tail = util.parse_cmdline2(line, ['send', 'receive', 'help', 'show', 'set'], log)

        x = self.xmodem

        if cmd == 'send':
            x.send_file(tail)
        elif cmd == 'receive':
            x.receive_file(tail)
        elif cmd == 'show':
            x.show_config(tail)
        elif cmd == 'set':
            x.set_config(tail)
        elif cmd == 'help':
            x.help(tail)
        else:
            log.i('Invalid command {}'.format(line))



class KermitCmds:

    def __init__(self, transport):
        self.kermit = kermit.Kermit(transport)


    def _hpcalc(self):
        log.i('Press Ctrl-C to quit')
        try:
            while True:
                self.kermit.send_command(raw_input('{}{}'.format('hpcalc', PROMPTER)))
        except KeyboardInterrupt:
            log.i('')


    def _remote(self, line):
        cmd, tail = util.parse_cmdline2(line, kermit.kermit_cmds['remote'].subcmds, log)

        k = self.kermit

        if cmd == 'cwd':
            k.remote_cwd(tail)
        elif cmd == 'delete':
            k.remote_delete(tail)
        elif cmd == 'directory':
            k.remote_directory()
        elif cmd == 'host':
            if tail:
                k.remote_host(tail)
            else:
                self._hpcalc()
        elif cmd == 'path': # Not in Kermit specification
            k.remote_path()
        elif cmd == 'space':
            k.remote_space()
        elif cmd == 'type':
            k.remote_type(tail)
        else:
            log.i('Invalid remote command: {}'.format(line))


    def _local(self, line):
        cmd, tail = util.parse_cmdline2(line, kermit.kermit_cmds['local'].subcmds, log)

        k = self.kermit

        if cmd == 'cwd':
            k.local_cwd(tail)
        elif cmd == 'delete':
            k.local_delete(tail)
        elif cmd == 'directory':
            k.local_directory(tail)
        elif cmd == 'path':
            k.local_path()
        elif cmd == 'push':
            k.local_push()
        elif cmd == 'run':
            k.local_run(tail)
        elif cmd == 'space':
            k.local_space()
        elif cmd == 'type':
            k.local_type(tail)
        else:
            log.i('Invalid local command: {}'.format(line))


    def exec_line(self, line):
        k = self.kermit
        while line:
            cmd, tail = util.parse_cmdline2(line, kermit.kermit_cmds.keys(), log)
            if cmd == 'help':
                k.help(tail)
            elif cmd == 'finish':
                k.finish()
            elif cmd == 'send':
                k.send(tail)
            elif cmd == 'get':
                k.get(tail)
            elif cmd == 'receive':
                k.receive()
            elif cmd == 'remote':
                self._remote(tail)
            elif cmd == 'server':
                k.server(tail)
            elif cmd == 'take':
                k.take(tail)
            elif cmd == 'echo':
                k.echo(tail)
            elif cmd == 'local':
                self._local(tail)
            elif cmd == 'set':
                k.set(tail)
            elif cmd == 'show':
                k.show(tail)
            elif cmd == '':
                self._local(line)

            line = k.next_cmd()



class Dispatcher:

    def __init__(self, args=default_args):
        self.prompt = PROMPTER
        self.scripts = []
        self.arg_cmds = []
        self.arg_flag = True
        self.cmd_proc = None

        self.done = False

        self.config = {
            'exit-on-error':  CV(C['exit-on-error']['false'], bool, 'Exit on error'),
            'trace-on-error': CV(C['trace-on-error']['true'], bool, 'Print stack trace on error'),
            'local-echo':     CV(C['local-echo']['true'], bool, 'Echo command line locally'),
            'log-level':      CV(5, int, 'Set log level'),
            'wav-prefix':     CV('', str, 'Set wav prefix'),
        }

        self.transport = transport.Transport(args.showinit, args.wavprefix, args.framerate, args.sensitivity)

        self.kermit_cmd_proc = KermitCmds(self.transport)
        self.serial_cmd_proc = SerialCmds(self.transport)
        self.xmodem_cmd_proc = XmodemCmds(self.transport)

        init_file = args.init
        if init_file and (init_file != DEFAULT_INI_FILE or os.path.exists(init_file)):
            log.i('Reading init script {}'.format(init_file))
            try:
                self.scripts = read_scripts(init_file)
            except IOError:
                log.e('Error reading {}'.format(init_file))

        self.arg_cmds = self.proc_args(args)


    def proc_args(self, args):
        s = []
        if args.serial:
            if args.receive:
                if args.timeout:
                    s.append('serial set mode timeout')
                    s.append('serial set timeout {}'.format(args.timeout))
                elif args.watchars:
                    s.append('serial set mode watchars')
                    s.append('serial set watchars {}'.format(args.watchars))
                s.append('serial receive {}'.format(args.receive))
            elif args.send:
                s.append('serial send file {}'.format(args.send))
            elif args.chars:
                s.append('serial send chars {}'.format(args.chars))
        elif args.xmodem:
            if args.send:
                s.append('xmodem send {}'.format(args.send))
            elif args.receive:
                s.append('xmodem receive {}'.format(args.receive))
        else:
            if args.text and args.send:
                s.append('kermit set transfer text')
            if args.send:
                val = 'kermit send {}'.format(args.send)
                if args.name:
                    val += ' as {}'.format(args.name)
                s.append(val)
            elif args.receive:
                s.append('kermit receive {}'.format(args.receive))
            elif args.get:
                s.append('kermit get {}'.format(args.get))

        if len(s) > 0:
            s.append('quit')
        else:
            if args.xmodem:
                s.append('xmodem')
            elif args.serial:
                s.append('serial')
            elif args.kermit and not (args.text or args.send or args.receive):
                s.append('kermit')

        return s


    def start_transport(self):
        self.transport.start_it()


    def stop_transport(self):
        self.transport.stop_it()


    def next_script_cmd(self):
        cmd = util.get_script_cmd(self.scripts)
        if not cmd:
            if self.arg_flag and self.cmd_proc and self.arg_cmds:
                self.arg_flag = False
                self.quit()
            cmd = util.get_script_cmd(self.arg_cmds)
        return cmd


    def listen(self, tail=''):
        parts = (tail + ' x x').split()[0:2]
        nap_count = util.parse_int(parts[0], 30)
        nap_time = util.parse_float(parts[1], 1)
        for i in range(0, nap_count):
            log.i([chr(b) for b in self.transport.peek()])
            time.sleep(nap_time)


    def peek(self):
        log.i(self.transport.peek())


    def wait(self, tail=''):
        secs = util.parse_float(tail, 10.0)
        log.i('Waiting for {} seconds'.format(secs))
        time.sleep(secs)


    def set_config(self, line):
        util.set_config(line, self.config, C, log)
        cmd, tail = util.parse_cmdline2(line, self.config, log)
        if cmd == 'log-level':
            log.set_log_level(self.config['log-level'].value)
        if cmd == 'wav-prefix':
            self.transport.set_wav_prefix(tail)


    def show_config(self, line):
        util.show_config(self.config, C, log, line)


    def echo(self, line):
        log.i(line)


    def help(self, line=''):
        util.show_help(log, line, hpcomm_cmds, self.config, C)


    def _procit(self, tail, proc, proc_name):
        if len(tail) > 0:
            proc.exec_line(tail)
        else:
            self.cmd_proc = proc
            self.prompt = '{}{}'.format(proc_name, PROMPTER)


    def proc_serial(self, tail=''):
        self._procit(tail, self.serial_cmd_proc, 'serial')


    def proc_kermit(self, tail=''):
        self._procit(tail, self.kermit_cmd_proc, 'kermit')


    def proc_xmodem(self, tail=''):
        self._procit(tail, self.xmodem_cmd_proc, 'xmodem')


    def _sub_proc(self, tail):
        if self.cmd_proc:
            self.cmd_proc.exec_line(tail)
            return True
        return False


    def script(self, tail):
        cmds = read_scripts(tail)
        for cmd in cmds[::-1]:
            self.scripts.insert(0, cmd)


    def quit(self):
        if self.cmd_proc:
            self.prompt = PROMPTER
            self.cmd_proc = None
        else:
            self.done = True


    def is_done(self):
        return self.done


    def force_done(self):
        self.done = True


    def read_line(self):
        script_line = self.next_script_cmd()

        if script_line and self.is_local_echo():
            # Note: log.*() will not work if logging is low
            log.i('={}{}'.format(self.prompt, script_line))

        try:
            line = script_line or raw_input(self.prompt)
        except EOFError as ee:
            # Piped data will throw this error.
            self.force_done()
            line = ''

        return line


    def exec_line(self, line):
        if not line.strip():
            return

        d = self
        cmd, tail = util.parse_cmdline2(line, hpcomm_cmds.keys(), log)

        if cmd == 'quit':
            d.quit()
            return

        if d._sub_proc(line):
            return

        if cmd == 'echo':
            d.echo(tail)
        elif cmd == 'serial':
            d.proc_serial(tail)
        elif cmd == 'kermit':
            d.proc_kermit(tail)
        elif cmd == 'xmodem':
            d.proc_xmodem(tail)
        elif cmd == 'help':
            d.help(tail)
        elif cmd == 'listen':
            d.listen(tail)
        elif cmd == 'peek':
            d.peek()
        elif cmd == 'wait':
            d.wait(tail)
        elif cmd == 'script':
            d.script(tail)
        elif cmd == 'show':
            d.show_config(tail)
        elif cmd == 'set':
            d.set_config(tail)
        else:
            log.i('Unrecognized command: {}'.format(line))


    def read_and_exec(self):
        """Reads a command and executes it."""
        self.exec_line(self.read_line())


    def _get_config_val(self, key):
        if key in self.config:
            return self.config[key].value
        return None


    def is_local_echo(self):
        return self._get_config_val('local-echo')


    def is_exit_on_error(self):
        return self._get_config_val('exit-on-error')


    def is_trace_on_error(self):
        return self._get_config_val('trace-on-error')
