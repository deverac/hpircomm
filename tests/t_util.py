import unittest
import logging

import src.util as util
import src.log

from mock import patch, Mock, MagicMock

from tests.sert import sert, TAttrBag

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



class TestAttrBag(unittest.TestCase):

    def test_should_create_bag(self):
        bag = util.AttrBag(key1='val1', key2='val2')
        sert(bag.key1).to_equal('val1')
        sert(bag.key2).to_equal('val2')


    def test_should_compare_equal(self):
        bag1 = util.AttrBag(key1='val1', key2='val2')
        bag2 = util.AttrBag(key1='val1', key2='val2')

        sert(bag1 == bag2).is_true()


    def test_should_compare_unequal(self):
        bag1 = util.AttrBag(key1='val1', key2='val2')
        bag2 = util.AttrBag(key1='valx', key2='val2')

        sert(bag1 != bag2).is_true()


    def test_should_display(self):
        bag1 = util.AttrBag(key1='val1', key2='val2')

        sert(repr(bag1)).to_equal("AttrBag(key1='val1', key2='val2')")



class TestCmdVal(unittest.TestCase):

    def test_should_create(self):
        cmd_val = src.util.CmdVal('some help', '[PARAM]', { 'a': 1, 'b': 2 })

        sert(cmd_val.helptext).to_equal('some help')
        sert(cmd_val.params).to_equal('[PARAM]')
        sert(cmd_val.subcmds).to_equal({ 'a': 1, 'b': 2 })



class TestConfigVal(unittest.TestCase):

    def test_should_create(self):
        cmd_val = src.util.ConfigVal(5, int, 'some config help')

        sert(cmd_val.value).to_equal(5)
        sert(cmd_val.validator).to_equal(int)
        sert(cmd_val.helptext).to_equal('some config help')



class TestCmd(unittest.TestCase):

    def test_should_match2(self):
        for cmd in util.HP48_CMDS:
            if cmd not in HP48_CMDS:
                raise Exception(cmd + ' not found')


    def test_should_match(self):
            sert(len(util.HP48_CMDS)).to_equal(len(HP48_CMDS))



class TestHpName(unittest.TestCase):

    def test_should_remove_illegal_chars(self):
        obj_sep = ' .,@'
        obj_delim = """#[]"'{}():_""" # Not included: [ left-chevron, right-chevron ]
        math_sym = '+-*/^=<>!' # Not included: [ square-root, lte, gte, not-equal, greek-lower-case-delta, integration]

        illegal_chars = obj_sep + obj_delim + math_sym
        for ch in illegal_chars:
            name = 'abc'+ch
            sert(util.get_valid_hp_name(name, src.log)).to_equal('abc')


    def test_should_remove_leading_digits(self):
        for n in range(0,100):
            name = str(n) + 'abc'
            sert(util.get_valid_hp_name(name, src.log)).to_equal('abc')


    def test_should_trim_length(self):
        name = 'a' * 128
        sert(len(util.get_valid_hp_name(name, src.log))).to_equal(127)


    def test_should_exclude_hp_commands(self):
        for cmd in HP48_CMDS:
            sert(util.get_valid_hp_name(cmd, src.log)).to_equal('')



class TestQuote(unittest.TestCase):

    def test_should_add_quotes(self):
        sert(util.quote('abc')).to_equal('"abc"')



class TestFilterText(unittest.TestCase):

    def test_should_filter_text(self):
        for n in range(0,256):
            txt = 'a'+chr(n)
            if n == 10 or (n > 31 and n < 128):
                sert(util.filter_text(txt)).to_equal(txt)
            else:
                sert(util.filter_text(txt)).to_equal('a')



class TestTxtToHpBin(unittest.TestCase):

    def test_should_convert_text_to_hp_object(self):
        bin = util.txt_to_hpbin('abc')
        actual = [hex(b) for b in bytearray(bin)]
        expected = [hex(b) for b in bytearray('HPHP48-P\x2C\x2A\xB0\x00\x00abc\x00')]
        sert(actual).to_equal(expected)



class TestParseInt(unittest.TestCase):

    def test_should_parse_int(self):
        sert(util.parse_int('7', 3)).to_equal(7)

    def test_should_handle_invalid_value(self):
        sert(util.parse_int('not_an_int', 3)).to_equal(3)



class TestParseFloat(unittest.TestCase):

    def test_should_parse_float(self):
        sert(util.parse_float('7.2', 3.1)).to_equal(7.2)


    def test_should_handle_invalid_value(self):
        sert(util.parse_float('not_a_float', 6.4)).to_equal(6.4)



class TestParseBoolstr(unittest.TestCase):

    def test_should_parse_t(self):
        sert(util.parse_boolstr('t')).to_equal('true')
        sert(util.parse_boolstr('T')).to_equal('true')


    def test_should_parse_1(self):
        sert(util.parse_boolstr('1')).to_equal('true')


    def test_should_parse_true(self):
        sert(util.parse_boolstr('true')).to_equal('true')
        sert(util.parse_boolstr('TRUE')).to_equal('true')
        sert(util.parse_boolstr('tRuE')).to_equal('true')


    def test_should_parse_f(self):
        sert(util.parse_boolstr('f')).to_equal('false')
        sert(util.parse_boolstr('F')).to_equal('false')


    def test_should_parse_0(self):
        sert(util.parse_boolstr('0')).to_equal('false')


    def test_should_parse_false(self):
        sert(util.parse_boolstr('false')).to_equal('false')
        sert(util.parse_boolstr('FALSE')).to_equal('false')
        sert(util.parse_boolstr('fAlSe')).to_equal('false')


    def test_should_ignore_invalid_val(self):
        sert(util.parse_boolstr('not_a_bool')).to_equal('not_a_bool')



class TestFormatSi(unittest.TestCase):

    # Note: Use of 'E' is a float. Use of '**' is an int.
    # 1E21 == 10**21
    # 1E22 == 10**22
    # 1E23 != 10**23
    # 1E24 != 10**24

    def test_should_format_number(self):
        sert(util.format_si(999)).to_equal('    999 ')


    def test_should_format_k(self):
        sert(util.format_si(10**3)).to_equal('  1.000K')


    def test_should_format_m(self):
        sert(util.format_si(10**6)).to_equal('  1.000M')


    def test_should_format_g(self):
        sert(util.format_si(10**9)).to_equal('  1.000G')


    def test_should_format_t(self):
        sert(util.format_si(10**12)).to_equal('  1.000T')


    def test_should_format_p(self):
        sert(util.format_si(10**15)).to_equal('  1.000P')


    def test_should_format_e(self):
        sert(util.format_si(10**18)).to_equal('  1.000E')


    def test_should_format_z(self):
        sert(util.format_si(10**21)).to_equal('  1.000Z')


    def test_should_format_y(self):
        sert(util.format_si(10**24)).to_equal('  1.000Y')


    def test_should_handle_overflow(self):
        sert(util.format_si(10**27)).to_equal('999.999?')



class TestKeyForVal(unittest.TestCase):

    def test_should_return_val(self):
        sert(util.key_for_val({'a': 3, 'b': 4}, 4)).to_equal('b')


    def test_should_return_none(self):
        sert(util.key_for_val({'a': 3, 'b': 4}, 5)).to_equal(None)



class TestCountOnes(unittest.TestCase):

    def test_should_count_ones(self):
        sert(util.count_ones(126)).to_equal(6)



class TestSetParity(unittest.TestCase):

    def test_should_set_none_parity(self):
        for n in range(0, 127):
            sert(util.set_parity([n], 0)).to_equal([n])


    def test_should_set_odd_parity(self):
        evens = [0, 3, 5, 6, 9, 10, 12, 15]
        for n in range(0, 127):
            lo_is_even = (n & 0x0F) in evens
            hi_is_even = (n >> 4) in evens

            lo_is_odd = not lo_is_even
            hi_is_odd = not hi_is_even

            val = util.set_parity([n], 1)
            if (hi_is_even and lo_is_even) or (hi_is_odd and lo_is_odd):
                sert(val[0] & 0x80).to_equal(0x80)
            else:
                sert(val[0] & 0x80).to_equal(0x00)


    def test_should_set_even_parity(self):
        evens = [0, 3, 5, 6, 9, 10, 12, 15]
        for n in range(0, 127):
            lo_is_even = (n & 0x0F) in evens
            hi_is_even = (n >> 4) in evens

            lo_is_odd = not lo_is_even
            hi_is_odd = not hi_is_even

            val = util.set_parity([n], 2)
            if (hi_is_even and lo_is_even) or (hi_is_odd and lo_is_odd):
                sert(val[0] & 0x80).to_equal(0x00)
            else:
                sert(val[0] & 0x80).to_equal(0x80)


    def test_should_set_mark_parity(self):
        for n in range(0, 127):
            val = util.set_parity([n], 3)
            sert(val[0] & 0x80).to_equal(0x80)


    def test_should_set_space_parity(self):
        for n in range(0, 127):
            val = util.set_parity([n], 4)
            sert(val[0] & 0x80).to_equal(0x00)


    def test_should_return_empty_list_for_invalid_parity_value(self):
        for n in range(0, 127):
            sert(util.set_parity([n], -1)).to_equal([])



class TestCalcMaxWidth(unittest.TestCase):

    def test_should_calculate_max_width(self):
        sert(util.calc_max_width(['aaa', 'bbbb', 'cc'])).to_equal(4)



class TestCalcMaxCmdWidth(unittest.TestCase):

    def test_should_calculate_max_cmd_width(self):
        cmds = {
            'cmd1': TAttrBag(helptext='aaaaaa', params='bb', subcmds='cc'),
            'cmd2': TAttrBag(helptext='ddd', params='eeee', subcmds='fffffff'),
        }
        sert(util.calc_max_cmd_width(cmds)).to_equal(len('cmd2' + ' ' + 'eeee'))


    def test_should_handle_none_params(self):
        cmds = {
            'cmd1': TAttrBag(helptext='aaaaaa', params='bb', subcmds='cc'),
            'cmd2': TAttrBag(helptext='ddd', params=None, subcmds='fffffff'),
        }
        sert(util.calc_max_cmd_width(cmds)).to_equal(len('cmd1' + ' ' + 'bb'))



class TestGetCmdAndTail(unittest.TestCase):

    def test_should_get_cmd_and_tail(self):
        sert(util.get_cmd_and_tail('abc def ghi jkl')).to_equal(('abc', 'def ghi jkl'))


    def test_should_strip_cmd_and_tail(self):
        sert(util.get_cmd_and_tail('   abc    def  ghi   ')).to_equal(('abc', 'def  ghi'))


    def test_should_handle_missing_tail(self):
        sert(util.get_cmd_and_tail('  aaa ')).to_equal(('aaa', ''))


    def test_should_hande_missing_cmd(self):
        sert(util.get_cmd_and_tail('')).to_equal(('', ''))


    def test_should_hande_blank(self):
        sert(util.get_cmd_and_tail('    ')).to_equal(('', ''))



class TestFindMatchingCmds(unittest.TestCase):

    def setUp(self):
        self.cmds = {
            'a_cmd': TAttrBag(helptext='ddd', params=None, subcmds='fff'),
            'cmd2': TAttrBag(helptext='mmm', params=None, subcmds='nnn'),
            'cmd1': TAttrBag(helptext='aaa', params=None, subcmds='ccc'),
            'another_cmd': TAttrBag(helptext='kkk', params=None, subcmds='lll'),
            'cmd3': TAttrBag(helptext='ggg', params=None, subcmds='iii'),
        }


    def test_should_return_matching_commands(self):
        sert(util.find_matching_cmds('cm', self.cmds)).to_equal(['cmd1', 'cmd2', 'cmd3'])
        sert(util.find_matching_cmds('a', self.cmds)).to_equal(['a_cmd', 'another_cmd'])


    def test_should_return_all_cmds_for_empty_cmd(self):
        sert(util.find_matching_cmds('', self.cmds)).to_equal(['a_cmd', 'another_cmd', 'cmd1', 'cmd2', 'cmd3'])


    def test_should_return_sorted_cmds(self):
        all_cmds = util.find_matching_cmds('', self.cmds)
        for i in range(1, len(all_cmds)):
            sert(all_cmds[i-1] < all_cmds[i]).is_true()


    def test_should_return_empty_when_no_match(self):
        sert(util.find_matching_cmds('invalid_cmd', self.cmds)).to_equal([''])


    def test_should_return_match(self):
        sert(util.find_matching_cmds('cmd2', self.cmds)).to_equal(['cmd2'])



class TestParseCmdLine(unittest.TestCase):

    def setUp(self):
        self.fields = ['cmd2', 'cmd3', 'a_cmd', 'cmd1', 'another_cmd']


    def test_should_return_completed_cmd_and_tail(self):
        sert(util.parse_cmdline('an ee ff', self.fields)).to_equal(('another_cmd', 'ee ff'))


    def test_should_return_multi_cmds_and_tail(self):
        sert(util.parse_cmdline('cm ee ff', self.fields, True)).to_equal((['cmd1', 'cmd2', 'cmd3'], 'ee ff'))



class TestFmtStr(unittest.TestCase):

    def test_should_fmtstr(self):
        lpad = ''
        key_wid = 5
        sert(util.fmtstr(lpad, 'key', 'val', key_wid)).to_equal('  key  : val')


    def test_should_show_lpad(self):
        lpad = '    '
        key_wid = 5
        sert(util.fmtstr(lpad, 'key', 'val', key_wid)).to_equal('      key  : val')


    def test_should_show_key_when_key_exceeds_key_wid(self):
        lpad = ''
        key_wid = 1
        sert(util.fmtstr(lpad, 'key', 'val', key_wid)).to_equal('  key: val')



class TestGetCfgMatches(unittest.TestCase):

    def setUp(self):
        self.cfg = {
            'cow': TAttrBag(value='brown', validator=str, helptext='cow help'),
            'dogs': {
                'pug': TAttrBag(value=6, validator=int, helptext='pug help'),
                'husky': TAttrBag(value='gray', validator=str, helptext='husky help'),
                'poodle': TAttrBag(value='white', validator=str, helptext='poodle help'),
            },
            'cat': TAttrBag(value=2, validator=int, helptext='cat help'),
        }


    def test_should_return_matches(self):
        cfg, tail = util.get_cfg_matches('c', self.cfg)

        sert(len(cfg)).to_equal(2)
        sert(cfg.keys()).to_equal(['cow', 'cat'])
        sert(tail).to_equal('')


    def test_should_handle_bad_key(self):
        cfg, tail = util.get_cfg_matches('bad_key some_val', self.cfg)

        sert(cfg).to_equal({})
        sert(tail).to_equal('some_val')



class TestShowConfig(unittest.TestCase):

    def setUp(self):
        self.cfg = {
            'cow': TAttrBag(value='brown', validator=str, helptext='cow help'),
            'dogs': {
                'pug': TAttrBag(value=6, validator=int, helptext='pug help'),
                'husky': TAttrBag(value='gray', validator=str, helptext='husky help'),
                'poodle': TAttrBag(value='white', validator=str, helptext='poodle help'),
            },
            'cat': TAttrBag(value=2, validator=int, helptext='cat help'),
        }

        self.const_dct = {
            'cat': {'black': 1, 'orange': 2, 'white': 3},
            'pug': {'beige': 5, 'blond': 6},
        }

        orange_val = 2
        sert(self.cfg['cat'].value).to_equal(orange_val)
        sert(self.const_dct['cat']['orange']).to_equal(orange_val)

        blond_val = 6
        sert(self.cfg['dogs']['pug'].value).to_equal(blond_val)
        sert(self.const_dct['pug']['blond']).to_equal(blond_val)


    def test_should_show_config(self):
        mock_log = Mock()

        util.show_config(self.cfg, self.const_dct, mock_log)

        sert(mock_log.i).called_n_times(6)
        sert(mock_log.i).nth_call_called_with(1, '  cat : orange')
        sert(mock_log.i).nth_call_called_with(2, '  cow : brown')
        sert(mock_log.i).nth_call_called_with(3, '  dogs: ')
        sert(mock_log.i).nth_call_called_with(4, '      husky : gray')
        sert(mock_log.i).nth_call_called_with(5, '      poodle: white')
        sert(mock_log.i).nth_call_called_with(6, '      pug   : blond')


    def test_should_show_single_config_val(self):
        mock_log = Mock()

        util.show_config(self.cfg, self.const_dct, mock_log, 'cow')

        sert(mock_log.i).called_once_with('  cow: brown')


    def test_should_show_multiple_config_vals(self):
        mock_log = Mock()

        util.show_config(self.cfg, self.const_dct, mock_log, 'c')

        sert(mock_log.i).called_twice()
        sert(mock_log.i).nth_call_called_with(1, '  cat: orange')
        sert(mock_log.i).nth_call_called_with(2, '  cow: brown')


    def test_should_show_single_child_config_val(self):
        mock_log = Mock()

        util.show_config(self.cfg, self.const_dct, mock_log, 'dogs pug')

        sert(mock_log.i).called_twice()
        sert(mock_log.i).nth_call_called_with(1, '  dogs: ')
        sert(mock_log.i).nth_call_called_with(2, '      pug: blond')


    def test_should_show_multiple_child_config_vals(self):
        mock_log = Mock()

        util.show_config(self.cfg, self.const_dct, mock_log, 'do p')

        sert(mock_log.i).called_n_times(3)
        sert(mock_log.i).nth_call_called_with(1, '  dogs: ')
        sert(mock_log.i).nth_call_called_with(2, '      poodle: white')
        sert(mock_log.i).nth_call_called_with(3, '      pug   : blond')



class TestShowHelp(unittest.TestCase):

    def setUp(self):
        self.cmds = {
            'dir':  TAttrBag(helptext='Help for dir', params=None, subcmds=None),
        }

        self.cfg = {
            'timer': TAttrBag(value=1, validator=int, helptext='Help for timer'),
        }

        self.const_dct = {
            'timer': {'on': 1, 'off': 2},
        }



    def test_should_show_all_config_and_commands(self):
        mock_log = Mock()

        util.show_help(mock_log, '', self.cmds, self.cfg, self.const_dct)

        mi = mock_log.i
        sert(mi).called_n_times(4)
        sert(mi).nth_call_called_with(1, '\n  === CONFIG ===')
        sert(mi).nth_call_called_with(2, '  timer: Help for timer {off, on}')
        sert(mi).nth_call_called_with(3, '\n  === COMMANDS ===')
        sert(mi).nth_call_called_with(4, '  dir : Help for dir')



class TestShowConfigHelp(unittest.TestCase):

    def setUp(self):
        self.cfg = {
            'cow': TAttrBag(value='brown', validator=str, helptext='cow help'),
            'dogs': {
                'pug': TAttrBag(value=6, validator=int, helptext='pug help'),
                'husky': TAttrBag(value='gray', validator=str, helptext='husky help'),
                'poodle': TAttrBag(value='white', validator=str, helptext='poodle help'),
            },
            'cat': TAttrBag(value=2, validator=int, helptext='cat help'),
        }

        self.const_dct = {
            'cat': {'black': 1, 'orange': 2, 'white': 3},
            'pug': {'beige': 5, 'blond': 6},
        }

        orange_val = 2
        sert(self.cfg['cat'].value).to_equal(orange_val)
        sert(self.const_dct['cat']['orange']).to_equal(orange_val)

        blond_val = 6
        sert(self.cfg['dogs']['pug'].value).to_equal(blond_val)
        sert(self.const_dct['pug']['blond']).to_equal(blond_val)


    def test_should_show_config_help(self):
        mock_log = Mock()

        util.show_config_help(mock_log, self.cfg, self.const_dct)

        sert(mock_log.i).called_n_times(6)
        sert(mock_log.i).nth_call_called_with(1, '  cat : cat help {black, orange, white}')
        sert(mock_log.i).nth_call_called_with(2, '  cow : cow help')
        sert(mock_log.i).nth_call_called_with(3, '  dogs: ')
        sert(mock_log.i).nth_call_called_with(4, '      husky : husky help')
        sert(mock_log.i).nth_call_called_with(5, '      poodle: poodle help')
        sert(mock_log.i).nth_call_called_with(6, '      pug   : pug help {beige, blond}')


    def test_should_show_single_config_val(self):
        mock_log = Mock()

        util.show_config_help(mock_log, self.cfg, self.const_dct, 'cow')

        sert(mock_log.i).called_once_with('  cow: cow help')


    def test_should_show_multiple_config_vals(self):
        mock_log = Mock()

        util.show_config_help(mock_log, self.cfg, self.const_dct, 'c')

        sert(mock_log.i).called_twice()
        sert(mock_log.i).nth_call_called_with(1, '  cat: cat help {black, orange, white}')
        sert(mock_log.i).nth_call_called_with(2, '  cow: cow help')


    def test_should_show_single_child_config_val(self):
        mock_log = Mock()

        util.show_config_help(mock_log, self.cfg, self.const_dct, 'dogs pug')

        sert(mock_log.i).called_twice()
        sert(mock_log.i).nth_call_called_with(1, '  dogs: ')
        sert(mock_log.i).nth_call_called_with(2, '      pug: pug help {beige, blond}')


    def test_should_show_multiple_child_config_vals(self):
        mock_log = Mock()

        util.show_config_help(mock_log, self.cfg, self.const_dct, 'do p')

        sert(mock_log.i).called_n_times(3)
        sert(mock_log.i).nth_call_called_with(1, '  dogs: ')
        sert(mock_log.i).nth_call_called_with(2, '      poodle: poodle help')
        sert(mock_log.i).nth_call_called_with(3, '      pug   : pug help {beige, blond}')



class TestShowCmdHelp(unittest.TestCase):

    def setUp(self):
        self.cmds = {
            'foo':  TAttrBag(helptext='foo help', params='[AA]', subcmds=None),
            'bar': TAttrBag(helptext='bar help', params=None, subcmds={
                'baz': TAttrBag(helptext='baz help', params='[BB]', subcmds=None),
                'bix': TAttrBag(helptext='bix help', params='[[CC] DD]', subcmds=None),
            }),
            'foz':  TAttrBag(helptext='foz help', params=None, subcmds=None),
        }


    def test_should_show_single_cmd_val(self):
        mock_log = Mock()

        util.show_cmd_help(mock_log, 'foo', self.cmds)

        sert(mock_log.i).called_once_with('  foo [AA]: foo help')


    def test_should_show_multiple_cmd_vals(self):
        mock_log = Mock()

        util.show_cmd_help(mock_log, 'f', self.cmds)

        sert(mock_log.i).called_twice()
        sert(mock_log.i).nth_call_called_with(1, '  foo [AA]: foo help')
        sert(mock_log.i).nth_call_called_with(2, '  foz     : foz help')


    def test_should_show_single_child_cmd_val(self):
        mock_log = Mock()

        util.show_cmd_help(mock_log, 'b bi', self.cmds)

        sert(mock_log.i).called_twice()
        sert(mock_log.i).nth_call_called_with(1, '  bar : bar help')
        sert(mock_log.i).nth_call_called_with(2, '      bix [[CC] DD]: bix help')


    def test_should_show_multiple_child_config_vals(self):
        mock_log = Mock()

        util.show_cmd_help(mock_log, 'b b', self.cmds)

        sert(mock_log.i).called_n_times(3)
        sert(mock_log.i).nth_call_called_with(1, '  bar : bar help')
        sert(mock_log.i).nth_call_called_with(2, '      baz [BB]     : baz help')
        sert(mock_log.i).nth_call_called_with(3, '      bix [[CC] DD]: bix help')



class TestGetScriptCmd(unittest.TestCase):

    def test_should_return_cmd(self):
        script = ['a', 'b', 'c']
        sert(util.get_script_cmd(script)).to_equal('a')
        sert(script).to_equal(['b', 'c'])


    def test_should_return_blank_val(self):
        sert(util.get_script_cmd([])).to_equal('')



class TestReadScript(unittest.TestCase):

    @patch('__builtin__.open')
    def test_should_read_file(self, mock_open):
        mock_open.return_value.readlines.return_value = ['a', 'b']

        val = util.read_script('abc.txt')

        sert(mock_open).called_with('abc.txt', 'r')
        sert(mock_open, 'close').called_once()


    @patch('__builtin__.open')
    def test_should_ret(self, mock_open):
        mock_open.return_value.readlines.return_value = ['a', 'b']

        val = util.read_script('abc.txt')

        sert(val).to_equal(['a', 'b'])


    @patch('__builtin__.open')
    def test_should_ignore_comments(self, mock_open):
        mock_open.return_value.readlines.return_value = [';g', 'h']

        val = util.read_script('abc.txt')

        sert(val).to_equal(['h'])


    @patch('__builtin__.open')
    def test_should_ignore_specified_comments(self, mock_open):
        mock_open.return_value.readlines.return_value = ['%e', 'f']

        val = util.read_script('abc.txt', '%')

        sert(val).to_equal(['f'])


    @patch('__builtin__.open')
    def test_should_ignore_blank_lines(self, mock_open):
        mock_open.return_value.readlines.return_value = ['c', '  ', 'd']

        val = util.read_script('abc.txt')

        sert(val).to_equal(['c', 'd'])



class TestSetConfig(unittest.TestCase):

    def setUp(self):
        self.cfg = {
            'sss': {
                'boolval': TAttrBag(value=True, validator=bool, helptext='boolval help'),
                'intval': TAttrBag(value=6, validator=int, helptext='intval help'),
                'strval': TAttrBag(value='abcde', validator=str, helptext='strval help'),
                'chrval': TAttrBag(value='@', validator=chr, helptext='chrval help'),
                'intra': TAttrBag(value=1, validator=int, helptext='intra help'),
            },
        }

        self.const_dct = {
            'boolval': {'true': True, 'false': False }
        }


    def test_should_set_bool(self):
        mock_log = Mock()
        sert(self.cfg['sss']['boolval'].value).is_true()

        val = util.set_config('sss boolval false', self.cfg, self.const_dct, mock_log)

        sert(val).is_true()
        sert(self.cfg['sss']['boolval'].value).is_false()


    def test_should_set_int(self):
        mock_log = Mock()
        sert(self.cfg['sss']['intval'].value).to_equal(6)

        val = util.set_config('ss intval 3', self.cfg, self.const_dct, mock_log)

        sert(val).is_true()
        sert(self.cfg['sss']['intval'].value).to_equal(3)


    def test_should_set_str(self):
        mock_log = Mock()
        sert(self.cfg['sss']['strval'].value).to_equal('abcde')

        val = util.set_config('ss strval fghijk', self.cfg, self.const_dct, mock_log)

        sert(val).is_true()
        sert(self.cfg['sss']['strval'].value).to_equal('fghijk')


    def test_should_set_chr(self):
        mock_log = Mock()
        sert(self.cfg['sss']['chrval'].value).to_equal('@')

        val = util.set_config('ss chrval %', self.cfg, self.const_dct, mock_log)

        sert(val).is_true()
        sert(self.cfg['sss']['chrval'].value).to_equal('%')


    def test_should_handle_invalid_bool(self):
        mock_log = Mock()
        sert(self.cfg['sss']['boolval'].value).is_true()

        val = util.set_config('sss boolval xxx', self.cfg, self.const_dct, mock_log)

        sert(val).is_false()
        sert(self.cfg['sss']['boolval'].value).is_true()
        sert(mock_log.i).called_once_with('sss:')
        sert(mock_log.e).called_once_with('Invalid value for "boolval": xxx')


    def test_should_handle_invalid_int(self):
        mock_log = Mock()
        sert(self.cfg['sss']['intval'].value).to_equal(6)

        val = util.set_config('sss intval xxx', self.cfg, self.const_dct, mock_log)

        sert(val).is_false()
        sert(self.cfg['sss']['intval'].value).to_equal(6)
        sert(mock_log.i).called_once_with('sss:')
        sert(mock_log.e).called_once_with('Invalid value for "intval": xxx')


    def test_should_handle_invalid_chr(self):
        mock_log = Mock()
        sert(self.cfg['sss']['chrval'].value).to_equal('@')

        val = util.set_config('sss chrval xxx', self.cfg, self.const_dct, mock_log)

        sert(val).is_false()
        sert(self.cfg['sss']['chrval'].value).to_equal('@')
        sert(mock_log.i).called_once_with('sss:')
        sert(mock_log.e).called_once_with('Invalid value for "chrval": xxx')


    def test_should_handle_multiple_matches(self):
        mock_log = Mock()

        val = util.set_config('sss in 3', self.cfg, self.const_dct, mock_log)

        sert(val).is_false()
        sert(mock_log.i).called_once_with('sss:')
        sert(mock_log.e).called_twice()
        sert(mock_log.e).nth_call_called_with(1, "Multiple matches for \"in\". Matches: ['intra', 'intval']")
        sert(mock_log.e).nth_call_called_with(2, "Name not found: in 3")


    def test_should_handle_invalid_name(self):
        mock_log = Mock()

        val = util.set_config('bad_name 5', self.cfg, self.const_dct, mock_log)

        sert(val).is_false()
        sert(mock_log.e).called_once_with('Name not found: bad_name 5')
