import shlex
import os
import glob
import datetime

import kprotocol
import util
import log

from util import CmdVal as Cmd


kermit_cmds = {
    'echo':     Cmd('Echo text', '[TEXT]'),
    'finish':   Cmd('Send Kermit Finish packet to HP48G'),
    'get':      Cmd('Get file from HP48G', 'FILE'),
    'help':     Cmd('Show this help'),
    'local':    Cmd('Execute command on local machine', None, {
        'cwd':       Cmd('Change working directory', '[DIR]'),
        'delete':    Cmd('Delete file', 'FILE'),
        'directory': Cmd('Display directory listing'),
        'path':      Cmd('Display the current path'),
        'push':      Cmd('Start local command interpreter'),
        'run':       Cmd('Run command', 'CMD'),
        'space':     Cmd('Show free and used space on disk'),
        'type':      Cmd('Display the contents of file', 'FILE'),
    }),
    'quit':     Cmd('Quit kermit protocol'),
    'receive':  Cmd('Receive file'),
    'remote':   Cmd('Execute command on remote host (HP48G)', None, {
        'cwd':       Cmd('Change working directory', '[DIR]'),
        'delete':    Cmd('Delete file', 'FILE'),
        'directory': Cmd('Display directory listing'),
        'host':      Cmd('Run command', '[CMD]'),
        'path':      Cmd('Display current path'),
        'space':     Cmd('Show free space'),
        'type':      Cmd('Display the contents of file', 'FILE'),
    }),
    'send':     Cmd('Send file', 'FILE'),
    'server':   Cmd('Change to DIR and start a Kermit server', '[DIR]'),
    'set':      Cmd('Set config value', 'NAME VAL'),
    'show':     Cmd('Show config values', '[NAME]'),
    'take':     Cmd('Read and execute Kermit commands from file', 'FILE'),
}


def filenames_from_specs(specs):
    lst = []
    for spec in shlex.split(specs):
        files = glob.glob(spec)
        lst.extend(files)
        if not files:
            log.i('No files found for {}'.format(spec))
    return lst


def parse_send_line(line):
    filename = None
    newname = None
    parts = shlex.split(line)
    is_rename = (len(parts) == 3) and (parts[1].lower() == 'as')
    if is_rename:
        files = glob.glob(parts[0])
        if len(files) == 1:
            filename = files[0]
            newname = parts[2]
    return is_rename, filename, newname



class Kermit(kprotocol.KermitProtocol):

    def __init__(self, transport):
        kprotocol.KermitProtocol.__init__(self, transport)
        self.takes = []


    def next_cmd(self):
        if self.takes:
            return self.takes.pop(0)
        return ''


    def finish(self):
        self._finish()


    def help(self, line=''):
        util.show_help(log, line, kermit_cmds, self.config, kprotocol.C)


    def send(self, line):
        is_text = self._is_transfer_text()
        is_rename, filename, newname = parse_send_line(line)
        if is_rename:
            self._send_file(filename, is_text, newname)
        else:
            filenames = filenames_from_specs(line)
            self._send_files(filenames, is_text)


    def get(self, line):
        hp_names = shlex.split(line)
        if hp_names:
            for hp_name in hp_names:
                self._get(hp_name)
        else:
            log.i('Invalid or missing name: {}'.format(line))


    def receive(self):
        self._receive()


    def server(self, path=None):
        orig_dir = None
        if path:
            orig_dir = os.getcwd()
            os.chdir(path)
        try:
            self._server()
        except KeyboardInterrupt:
            pass
        finally:
            if orig_dir:
                os.chdir(orig_dir)


    def remote_cwd(self, line):
        dir = '{ HOME }'
        if line:
            if line.startswith('{'):
                dir = line
            else:
                dir = '{ ' + line + ' }'
        self.send_command(dir + ' EVAL')


    def remote_delete(self, line):
        self._remote_eval(line.strip() + ' PURGE')


    def remote_directory(self):
        self._remote_eval('VARS')


    def remote_host(self, line):
        self.send_command(line.strip())


    def remote_path(self):
        self._remote_eval('PATH')


    def remote_space(self):
        self._remote_eval('MEM')


    def remote_type(self, line):
        self.send_command("'{}' RCL".format(line.strip()))


    def take(self, filename):
        f = open(filename, 'r')
        lines = f.readlines()
        f.close()
        cmd_lines = []
        for line in lines:
            stripped_line = line.strip()
            if stripped_line and not stripped_line.startswith(self.config['comment-char'].value):
                cmd_lines.append(stripped_line)
        cmd_lines.extend(self.takes)
        self.takes = cmd_lines


    def echo(self, line):
        log.i(line)


    def local_cwd(self, line):
        os.chdir(line.strip() or os.getcwd())


    def local_delete(self, line):
        dir = os.getcwd()
        specs = shlex.split(line)
        filenames = []
        for spec in specs:
            filenames.extend(glob.glob(spec))
        for name in filenames:
            file = os.path.join(dir, name)
            try:
                if os.path.isfile(file):
                    os.remove(file)
                elif os.path.isdir(file):
                    os.rmdir(file)
                else:
                    log.i('{} is not a file or dir. Ignored.'.format(file))
            except OSError:
                log.i('Delete {} failed.'.format(file))


    def local_directory(self, line=''):
        DIR_HEADER = '\x01'
        dir = os.getcwd()
        filenames = []
        if os.path.isdir(line) or not line:
            if line:
                dir = line
            filenames = os.listdir(dir)
        else:
            specs = shlex.split(line)
            for spec in specs:
                filenames.extend(glob.glob(spec))
        entries = []
        for filename in filenames:
            abspath = os.path.join(dir, filename)
            if os.path.isdir(abspath):
                filename = '{}[{}]'.format(DIR_HEADER, filename)
            s = os.stat(abspath)
            filesize = s.st_size
            lastmodified= s.st_mtime
            entries.append((lastmodified, filesize, filename))

        # Sort is stable.
        order_by = util.key_for_val(kprotocol.C['order-by'], self.config['order-by'].value)
        for ch in order_by[::-1]:
            if ch == 'd':
                entries.sort(key=lambda tup: tup[0])
            elif ch == 's':
                entries.sort(key=lambda tup: tup[1])
            elif ch == 'n':
                entries.sort(key=lambda tup: tup[2])
            else:
                log.e('Bad field char {}'.format(ch))

        oslope = self.config['oslope'].value
        for entry in entries[::oslope]:
            dt = datetime.datetime.fromtimestamp(entry[0]).strftime('%Y-%m-%d %H:%M')
            sz = util.format_si(entry[1])
            nm = entry[2]
            if nm.startswith(DIR_HEADER):
                nm = nm[1:]
            log.i('  {}  {}  {}'.format(dt, sz, nm))


    def local_path(self):
        log.i(os.getcwd())


    def local_push(self):
        shell = self.config['shell'].value
        if shell:
            os.system(shell)
        elif os.name == 'posix':
            os.system('bash')
        elif os.name == 'nt':
            os.system('command.com')
        else:
            log.e("Unknown shell. (Set the 'shell' config value)")


    def local_run(self, line):
        os.system(line)


    def local_space(self):
        st = os.statvfs(os.getcwd()) # Dep in 2.6. Removeed in 3.
        log.i(' Used: {}'.format(util.format_si((st.f_blocks - st.f_bavail) * st.f_frsize)))
        log.i(' Free: {}'.format(util.format_si(st.f_bavail * st.f_frsize)))
        log.i('Total: {}'.format(util.format_si(st.f_blocks * st.f_frsize)))

        # total, used, free = shutil.disk_usage("/")
        # print("Total: %d GB" % (total // (2**30)))
        # print("Used: %d GB" % (used // (2**30)))
        # print("Free: %d GB" % (free // (2**30)))

    def local_type(self, filename):
        if filename:
            f = open(filename, 'r')
            lines = f.read()
            f.close()
            log.i(lines)
        else:
            log.e('Missing filename')


    def show(self, line):
        util.show_config(self.config, kprotocol.C, log, line)


    def set(self, line):
        cmd, tail = util.parse_cmdline2(line, self.config, log)
        if not cmd:
            log.e('Name not found: {}'.format(line))
            return
        if cmd == 'receive':
            log.i('Cannot set receive')
            return
        util.set_config(line, self.config, kprotocol.C, log)
