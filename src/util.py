

# Derived from types.SimpleNamespace (Python 3.3)
class AttrBag:

    def __init__(self,**kw):
        self.__dict__.update(kw)

    def __repr__(self):
        keys = sorted(self.__dict__)
        items = ("{}={!r}".format(k, self.__dict__[k]) for k in keys)
        typ = self.__class__.__name__
        return "{}({})".format(typ, ", ".join(items))

    def __eq__(self, other):
        return self.__dict__ == other.__dict__



class CmdVal:

    def __init__(self, helptext, params=None, subcmds=None):
        self.helptext = helptext
        self.params = params
        self.subcmds = subcmds



class ConfigVal:

    def __init__(self, value, validator, helptext):
        self.value = value
        self.validator = validator
        self.helptext = helptext



# A non-exhaustive list of HP48 commands.
HP48_CMDS = [
'ABS', 'ACK', 'ACKALL', 'ACOS', 'ACOSH', 'ADD', 'ALOG', 'AMORT', 'AND',
'ANIMATE', 'ANS', 'APPLY', 'ARC', 'ARCHIVE', 'ARG', 'ASIN', 'ASINH', 'ASN',
'ASR', 'ATAN', 'ATANH', 'ATICK', 'ATTACH', 'AUTO', 'AXES', 'BAR', 'BARPLOT',
'BAUD', 'BEEP', 'BESTFIT', 'BIN', 'BINS', 'BLANK', 'BOX', 'BUFLEN', 'BYTES',
'CASE', 'CEIL', 'CENTR', 'CF', '%CH', 'CHOOSE', 'CHR', 'CKSM', 'CLEAR',
'CLKADJ', 'CLLCD', 'CLOSEIO', 'CLVAR', 'CMPLX', 'CNRM', 'COLCT',
'COMB', 'CON', 'COND', 'CONIC', 'CONJ', 'CONLIB', 'CONST', 'CONT', 'CONVERT',
'CORR', 'COS', 'COSH', 'COV', 'CR', 'CRDIR', 'CROSS', 'CSWP', 'CYLIN', 'DARCY',
'DATE', 'DATE+', 'DBUG', 'DDAYS', 'DEC', 'DECR', 'DEFINE', 'DEG', 'DELALARM',
'DELAY', 'DELKEYS', 'DEPND', 'DEPTH', 'DET', 'DETACH', 'DIFFEQ', 'DIR', 'DISP',
'DISPXY', 'DO', 'DOERR', 'DOLIST', 'DOSUBS', 'DOT', 'DRAW', 'DRAW3DMATRIX',
'DRAX', 'DROP', 'DROP2', 'DROPN', 'DTAG', 'DUP', 'DUP2', 'DUPDUP', 'DUPN', 'e',
'EDIT', 'EDITB', 'EGV', 'EGVL', 'ELSE', 'END', 'ENDSUB', 'ENG', 'EQNLIB', 'EQW',
'ERASE', 'ERR0', 'ERRM', 'ERRN', 'EVAL', 'EXP', 'EXPAN', 'EXPFIT', 'EXPM',
'EYEPT', 'FACT', 'FANNING', 'FAST3D', 'FC?', 'FC?C', 'FFT', 'FILER',
'FINDALARM', 'FINISH', 'FIX', 'FLASHEVAL', 'FLOOR', 'FONT6', 'FONT7', 'FONT8',
'FOR', 'FP', 'FREE', 'FREEZE', 'FS?', 'FS?C', 'FUNCTION', 'GAMMA', 'GET',
'GETI', 'GOR', 'GRAD', 'GRIDMAP', 'GROB', 'GROBADD', 'GXOR', 'HALT', 'HEAD',
'HEX', 'HISTOGRAM', 'HISTPLOT', 'HOME', 'i', 'IDN', 'IF',
'IFERR', 'IFFT', 'IFT', 'IFTE', 'IM', 'INCR', 'INDEP', 'INFORM', 'INPUT', 'INV',
'IP', 'ISOL', 'KERRM', 'KEY', 'KEYEVAL', 'KGET', 'KILL', 'LABEL', 'LAST',
'LASTARG', 'LIBEVAL', 'LIBS', 'LINE', 'LINFIT', 'LININ', 'LN', 'LNP1', 'LOG',
'LOGFIT', 'LQ', 'LR', 'LSQ', 'LU', 'MANT', 'MAP','MAX', 'MAXR', 'MCALC',
'MEAN', 'MEM', 'MENU', 'MERGE', 'MIN', 'MINEHUNT', 'MINIT', 'MINR', 'MITM',
'MOD', 'MROOT', 'MSGBOX', 'MSOLVR', 'MUSER', 'NDIST', 'NDUPN', 'NEG', 'NEWOB',
'NEXT', 'NIP', 'NOT', 'NOVAL', 'NSUB', 'NUM', 'NUMX', 'NUMY', 'OCT', 'OFF',
'OLDPRT', 'OPENIO', 'OR', 'ORDER', 'OVER', 'PARAMETRIC', 'PARITY', 'PARSURFACE',
'PATH', 'PCOEF', 'PCONTOUR', 'PCOV', 'PDIM', 'PERM', 'PEVAL', 'PGDIR', 'PICK',
'PICK3', 'PICT', 'PICTURE', 'PINIT', 'PIX?', 'PIXOFF', 'PIXON', 'PKT', 'PLOT',
'PLOTADD', 'PMAX', 'PMIN', 'POLAR', 'POP', 'POS', 'PR1', 'PREDV', 'PREDX',
'PREDY', 'PRLCD', 'PROMPT', 'PROMPTSTO', 'PROOT', 'PRST', 'PRSTC', 'PRVAR',
'PSDEV', 'Psi', 'PSI', 'PURGE', 'PUSH', 'PUT', 'PUTI', 'PVAR', 'PVARS', 'PVIEW',
'PWRFIT', 'qr', 'QR', 'QUAD', 'QUOTE', 'RAD', 'RAND', 'RANK', 'RANM', 'RATIO',
'RCEQ', 'RCI', 'RCIJ', 'RCL', 'RCLALARM', 'RCLF', 'RCLKEYS', 'RCLMENU', 'RCWS',
'RDM', 'RDZ', 'RE', 'RECN', 'RECT', 'RECV', 'RENAME', 'REPEAT', 'REPL', 'RES',
'RESTORE', 'REVLIST', 'RKF', 'RKFERR', 'RKFSTEP', 'RL', 'RLB', 'RND', 'RNRM',
'ROLL', 'ROLLD', 'ROOT', 'ROT', 'RR', 'RRB', 'RRK',
'RRKSTEP', 'RSBERR', 'RSD', 'RSWP', 'RULES', 'SAME', 'SBRK', 'SCALE', 'SCALEH',
'SCALEW', 'SCATRPLOT', 'SCATTER', 'SCHUR', 'SCI', 'SCONJ', 'SCROLL', 'SDEV',
'SEND', 'SEQ', 'SERVER', 'SF', 'SHOW', 'SIDENS', 'SIGN', 'SIN', 'SINH', 'SINV',
'SIZE', 'SL', 'SLB', 'SLOPEFIELD', 'SNEG', 'SNRM', 'SOLVEQN', 'SOLVER', 'SORT',
'SPHERE', 'SQ', 'SR', 'SRAD', 'SRB', 'SRECV', 'SREPL', 'START', 'STD', 'STEP',
'STEQ', 'STIME', 'STO', 'STO*', 'STO+', 'STO/', 'STO-', 'STOALARM', 'STOF',
'STOKEYS', 'STREAM', 'STWS', 'SUB', 'SVD', 'SVL', 'SWAP', 'SYSEVAL', '%T',
'TAIL', 'TAN', 'TANH', 'TAYLR', 'TDELTA', 'TEVAL', 'TEXT', 'THEN', 'TICKS',
'TIME', 'TINC', 'TLINE', 'TMENU', 'TOT', 'TRACE', 'TRAN', 'TRANSIO', 'TRN',
'TRNC', 'TRUTH', 'TSTR', 'TVARS', 'TVM', 'TVMBEG', 'TVMEND', 'TVMROOT', 'TYPE',
'UBASE', 'UFACT', 'UNPICK', 'UNROT', 'UNTIL', 'UPDIR', 'UTPC', 'UTPF', 'UTPN',
'UTPT', 'UVAL', 'VAR', 'VARS', 'VERSION', 'VISIT', 'VISITB', 'VTYPE', 'WAIT',
'WHILE', 'WIREFRAME', 'WSLOG', 'XCOL', 'XGET', 'XMIT', 'XOR', 'XPON', 'XPUT',
'XRECV', 'XRNG', 'XROOT', 'XSEND', 'XSERV', 'XVOL', 'XXRNG', 'YCOL', 'YRNG',
'YSLICE', 'YVOL', 'YYRNG', 'ZFACTOR', 'ZVOL'
]

def get_valid_hp_name(s, log):
    # Items in commented brackets are not included in the list because they
    # are (HP-defined) extended-ASCII chars.
    obj_sep = ' .,@'
    obj_delim = """#[]"'{}():_""" # [ left-chevron, right-chevron ]
    math_sym = '+-*/^=<>!' # [ square-root, lte, gte, not-equal, greek-lower-case-delta, integration]

    # Must not have illegal char
    illegal_chars = obj_sep + obj_delim + math_sym
    newname = ''.join([ch for ch in s if ch not in illegal_chars ])
    if s != newname:
        log.w('Stripped illegal char(s) from name')

    # Must not begin with a digit
    trimmed_digit = False
    while newname[0:1].isdigit():
        trimmed_digit = True
        newname = newname[1:]
    if trimmed_digit:
        log.w('Stripped leading digit(s)')

    # Must not use names of commands (e.g. SIN).
    if newname in HP48_CMDS:
        log.w(newname + ' is not allowed as a name.')
        newname = ''

    # Allowed, but reserved
    # 'EQ', 'CST', 'ALRMDAT', 'PPAR', 'VPAR', 'PRTPAR', 'IOPAR' # [ sum-DAT, sum-PAR ]
    # s1, s2, s3, ...
    # n1, n2, n3, ...
    # Names beginning with 'der'

    # 127 chars max
    return newname[0:127]


def quote(buf):
    return '"' + buf + '"'


def filter_text(buf):
    """Remove non-printable chars, except LF"""
    LINEFEED = 10
    filtered_buf = []
    for ch in buf:
        b = ord(ch)
        if b == LINEFEED or (b > 31 and b < 128):
            filtered_buf.append(ch)
    return ''.join(filtered_buf)


def txt_to_hpbin(txt):
    prolog_str = '02A2C'
    nib_len_prolog = len(prolog_str)
    size = (2 * len(txt)) + nib_len_prolog # Size in nibbles.
    s_and_p = (size << (4 * nib_len_prolog)) | int(prolog_str, 16)

    prolog_and_size = ''
    for i in range(0, 5): # Need 5 bytes (10 nibbles) for prolog and size.
        prolog_and_size += chr(s_and_p & 0xFF)
        s_and_p >>= 8

    bin_header = 'HPHP48-P' # 'P' can be replaced with any valid ROM version.
    bin_trailer = '\x00'
    return bin_header + prolog_and_size + txt + bin_trailer


def parse_int(val, default_val):
    try:
        return int(val)
    except:
        return default_val


def parse_float(val, default_val):
    try:
        return float(val)
    except:
        return default_val


def format_si(n):
    if n >= 1000:
        suffix = ['K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y']
        for i in range(0, len(suffix)):
            if n < 10**(3*(i+2)):
                div = 10**(3*(i+1))
                return "{:7.3f}{}".format((float(n)/div), suffix[i])
        return "{:7.3f}{}".format(999.999, '?')
    return "{:7} ".format(n)


def parse_boolstr(tail):
    if tail.lower() in ['1', 't', 'true']:
        return 'true'
    if tail.lower() in ['0', 'f', 'false']:
        return 'false'
    return tail


def key_for_val(dct, val):
    for key, value in dct.items():
         if val == value:
             return key
    return None


def count_ones(n):
    return len(bin(n & 0x7F)[2:].replace('0', ''))


def set_parity(bytes, parity):
    mod = []
    for byte in bytes:
        if parity == 0: # none
            mod.append(byte)
        elif parity == 1: # odd
            parity_bit = ((count_ones(byte) + 1) % 2) << 7
            mod.append(byte | parity_bit)
        elif parity == 2: # even
            parity_bit = (count_ones(byte) % 2) << 7
            mod.append(byte | parity_bit)
        elif parity == 3: # mark
            mod.append(byte | 0x80)
        elif parity == 4: # space
            mod.append(byte & 0x7F)
    return mod



def calc_max_width(lst):
    return max([len(i) for i in lst] or [0])


def calc_max_cmd_width(dct):
    return calc_max_width([(key + ' ' + (dct[key].params or '')) for key in dct.keys()])


def get_cmd_and_tail(line):
    a = line.strip().split(None, 1)
    if len(a) > 1:
        return a[0].strip(), a[1].strip()
    if len(a) > 0:
        return a[0].strip(), ''
    return '', ''


def find_matching_cmds(cmd, cmds):
    opts = []
    for c in cmds:
        if c.startswith(cmd):
            opts.append(c)
    if not opts:
        opts = ['']
    return sorted(opts)


def parse_cmdline(line, fields, multi=False):
    cmd, tail = get_cmd_and_tail(line)
    cmd_lst = find_matching_cmds(cmd, fields)
    if multi:
        return cmd_lst, tail
    return cmd_lst[0], tail


def parse_cmdline2(line, fields, log):
    '''
        Extract first word of line and search for match in fields. If multiple
        matches found, return None, None. Otherwise return the matched field
        (which may be empty) and remainer of line.
    '''
    cmd, tail = get_cmd_and_tail(line)
    cmd_lst = find_matching_cmds(cmd, fields)
    if len(cmd_lst) > 1:
        log.e('Multiple matches for "{}". Matches: {}'.format(cmd, cmd_lst))
        return None, None
    return cmd_lst[0], tail


def fmtstr(lpad, key, val, key_wid):
    return '  {}{:{wid}}: {}'.format(lpad, key, val, wid=key_wid)


def get_cfg_matches(line, cfg_dct):
    cfg = cfg_dct
    if line:
        cmds, line = parse_cmdline(line, cfg_dct.keys(), True)
        try:
            cfg = {cmd: cfg_dct[cmd] for cmd in cmds}
        except KeyError:
            cfg = {}
    return cfg, line


def show_config(cfg_dct, const_dct, log, line='', lpad=''):
    cfg, line = get_cfg_matches(line, cfg_dct)
    maxw = calc_max_width(cfg)
    for key, val in sorted(cfg.items()):
        if type(val) is dict:
            log.i(fmtstr(lpad, key, '', maxw))
            show_config(val, const_dct, log, line, lpad + '    ')
        else:
            vv = val.value
            if key in const_dct.keys():
                vv = key_for_val(const_dct[key], val.value)
            log.i(fmtstr(lpad, key, vv, maxw))


def show_help(log, line, cmds, cfg, const_dct):
    log.i('\n  === CONFIG ===')
    show_config_help(log, cfg, const_dct, line)

    log.i('\n  === COMMANDS ===')
    show_cmd_help(log, line, cmds)


def show_config_help(log, cfg_dct, const_dct={}, line='', lpad=''):
    cfg, line = get_cfg_matches(line, cfg_dct)
    maxw = calc_max_width(cfg)
    for key, val in sorted(cfg.items()):
        if type(val) is dict:
            log.i(fmtstr(lpad, key, '', maxw))
            show_config_help(log, val, const_dct, line, lpad + '    ')
        else:
            vv = val.helptext
            if key in const_dct.keys():
                vv = vv + ' {' + str(', '.join(sorted(const_dct[key].keys()))) + '}'
            log.i(fmtstr(lpad, key, vv, maxw))


def show_cmd_help(log, line, cmds, lpad=''):
    cmds, line = get_cfg_matches(line, cmds)
    maxw = calc_max_cmd_width(cmds)
    for key, cmdval in sorted(cmds.items()):
        cc = '{} {}'.format(key, (cmdval.params or ''))
        if type(cmdval.subcmds) is dict:
            log.i(fmtstr(lpad, cc, cmdval.helptext, maxw))
            show_cmd_help(log, line, cmdval.subcmds, lpad + '    ')
        else:
            log.i(fmtstr(lpad, cc, cmdval.helptext, maxw))


def get_script_cmd(scripts):
    if scripts:
        return scripts.pop(0)
    return ''


def read_script(filename, comment_char=';'):
    f = open(filename, 'r')
    lines = f.readlines()
    f.close()
    cmd_lines = []
    for line in lines:
        stripped_line = line.strip()
        if stripped_line and not stripped_line.startswith(comment_char):
            cmd_lines.append(stripped_line)
    return cmd_lines


def set_config(line, cfg, const_dct, log, lpad=''):
    cmd, tail = parse_cmdline2(line, cfg.keys(), log)
    if not cmd:
        log.e('Name not found: {}'.format(line))
        return False

    val = cfg[cmd]
    if type(val) is dict:
        log.i('{}{}:'.format(lpad, cmd))
        return set_config(tail, val, const_dct, log, lpad+'   ')
    else:
        if cmd in const_dct.keys():
            opts = const_dct[cmd]
            if cfg[cmd].validator == bool:
                tail = parse_boolstr(tail)
            if tail in opts.keys():
                cfg[cmd].value = opts[tail]
                show_config(cfg, const_dct, log, cmd, lpad)
                return True
            else:
                log.e('Invalid value for "{}": {}'.format(cmd, tail))
        else:
            try:
                if val.validator == chr:
                    tail = ord(tail)
                cfg[cmd].value = val.validator(tail)
                show_config(cfg, const_dct, log, cmd, lpad)
                return True
            except:
                log.e('Invalid value for "{}": {}'.format(cmd, tail))
    return False
