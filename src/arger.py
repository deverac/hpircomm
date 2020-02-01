#XXX
import argparse

def _format_arg(name):
    return '--'+name


def _validate_parsed_args(args, incompatibilities):
    dct = vars(args)
    for name1, lst in incompatibilities.items():
        for name2 in lst:
            arg1 = dct[name1]
            arg2 = dct[name2]
            if arg1 and arg2:
                return _format_arg(name1) + ' is incompatibile with ' + _format_arg(name2)
    return ''

# HelpFormatter copied and modified from https://stackoverflow.com/a/9643162
# Converts this:
#    -t SECS, --timeout SECS
# to this:
#    -t, --timeout SECS
class HpirHelpFormatter(argparse.HelpFormatter):

    # This handles positional and optional args, however, since only
    # optional args are used, the code for positional args has been
    # commented out.
    def _format_action_invocation(self, action):
        #if action.option_strings:
            parts = []

            # if the Optional doesn't take a value, format is:
            #    -s, --long
            if action.nargs == 0:
                parts.extend(action.option_strings)

            # if the Optional takes a value, format is:
            #    -s ARGS, --long ARGS
            else:
                default = self._get_default_metavar_for_optional(action)
                args_string = self._format_args(action, default)
                for option_string in action.option_strings:
                    parts.append(option_string)

                return '%s %s' % (', '.join(parts), args_string)

            return ', '.join(parts)
        # else:
        #     default = self._get_default_metavar_for_positional(action)
        #     metavar, = self._metavar_formatter(action, default)(1)
        #     return metavar

    def _get_default_metavar_for_optional(self, action):
        return action.dest.upper()


optionals = None


def _get_common_parser():
    global optionals
    parser = argparse.ArgumentParser(formatter_class=HpirHelpFormatter, description="Communicate with HP48G's IR port using soundcard as modem.", epilog='')
    parser._optionals.title = 'help'
    # Remove 'optional args' group. Due to the way we construct the
    # parser, this only includes the 'help' arg.
    optionals = parser._action_groups.pop()
    return parser


def _add_file_group(parser):
    group = parser.add_argument_group('file')
    group.add_argument('-s', '--send', action='store', metavar='FILE', help='Filename to send (or STDIN)')
    group.add_argument('-r', '--receive', action='store', metavar='FILE', help='Outfile filename (or STDOUT)')


def _add_serial_group(parser):
    group = parser.add_argument_group('serial')
    group.add_argument('-c', '--chars', action="store", help='Text to send')
    group.add_argument('-t', '--timeout', action="store", metavar='SECS', type=int, help='Receive until time has elapsed')
    group.add_argument('-w', '--watchars', action="store", metavar='TEXT', help='Receive until text has been received')


def _add_kermit_group(parser):
    group = parser.add_argument_group('kermit')
    group.add_argument('--text', action="store_true", help='Only send printable text and LF chars')
    group.add_argument('-n', '--name', action="store", help='Save to NAME when sending a file')
    group.add_argument('--get', action="store", metavar='VAR', help='Get VAR from calc')


def _add_config_group(parser):
    group = parser.add_argument_group('config')
    group.add_argument('--wavprefix', action="store", metavar='PREFIX', help='Write WAV files. Filenames will start with prefix')
    group.add_argument('--framerate', action="store", metavar='RATE', help='Set framerate of WAV files.', type=int)
    group.add_argument('--sensitivity', action="store", metavar='FLOAT', help='Rx sensitivity [0.0 - 1.0]', type=float)
    group.add_argument('--showinit', action="store_true", help='Show PyAudio initialization')
    group.add_argument('-l', '--log', action='count', help='Logging verbosity. See details below.', default=5)
    group.add_argument('--init', metavar='SCRIPT', action="store",  help = "Run script on start. Use '--init=' to disable. (default: hpir.ini)", default='hpir.ini')
    # Newlines are stripped from epilog before displaying.
    parser.epilog += 'The log level is like a volume slider bar for logging. Specifying once turns all logging off. Specifying five times is "max volume"; default is five.'
    parser.epilog += ' '
    parser.epilog += "When Kermit and '--receive' are used, FILE is required, but ignored; the filename is set by the sender."


def _add_protocol_group(parser):
    group = parser.add_argument_group('protocol')
    group.add_argument('--kermit', action="store_true",  help = "Use Kermit protocol (default)")
    group.add_argument('--xmodem', action="store_true",  help = "Use XMODEM protocol")
    group.add_argument('--serial', action="store_true",  help = "Use Serial port")


def _add_help_group(parser):
    if optionals:
        parser._action_groups.append(optionals)


def _get_parser():
    parser = _get_common_parser()
    _add_protocol_group(parser)
    _add_file_group(parser)
    _add_kermit_group(parser)
    _add_serial_group(parser)
    _add_config_group(parser)
    _add_help_group(parser)
    return parser


def check_args(sys_args):
    arg_incompatibilities = {
        'send': ['receive', 'chars', 'timeout', 'watchars', 'get'],
        'receive': ['chars', 'name', 'get', 'text'],
        'get': ['text'],
        'kermit': ['xmodem', 'serial', 'chars', 'timeout', 'watchars'],
        'xmodem': ['kermit', 'serial', 'text', 'name', 'chars', 'timeout', 'watchars', 'get'],
        'serial': ['kermit', 'xmodem', 'text', 'name', 'get'],
    }
    parser = _get_parser()
    parsed_args = parser.parse_args(sys_args)
    msg = _validate_parsed_args(parsed_args, arg_incompatibilities)
    if msg:
        parser.error(msg) # Exits.

    return parsed_args
