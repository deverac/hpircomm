import sys
import shlex

import src.arger
import src.hpcomm


# FIXME Double-check Receive-only is impossible

# FIXME Allow create wav for send-only
# FIXME Allow play wav to send


def read_args_from_init_file(filename, comment_char=';'):
    f = open(filename, 'r')
    lines = f.readlines()
    f.close()
    hdr = 'args: '
    arg_lines = []
    for line in lines:
        stripped_line = line.strip()
        if stripped_line.startswith(comment_char):
            arg_line = stripped_line[1:].strip()
            if arg_line.lower().startswith(hdr):
                arg_lines.append(arg_line[len(hdr):])
    return ' '.join(arg_lines)


def args_from_ini_file(ini_file, sys_argv):
    args = src.arger.check_args(sys_argv[1:])
    if args.init:
        ini_arg_line = read_args_from_init_file(ini_file)
        init_args = src.arger.check_args(shlex.split(ini_arg_line))
        for key in vars(args).keys():
            if key == 'init':
                continue
            arg_val = getattr(args, key)
            init_val = getattr(init_args, key)
            if (arg_val is None) and (init_val is not None):
                setattr(args, key, init_val)
    return args



def run_main(sys_argv):

    # args = src.arger.arg_ok(src.arger.get_parser, sys_argv[1:], ARG_INCOMPATIBILITIES)
    #args = src.arger.check_args(sys_argv[1:])

    #args = args_from_ini_file(ini_file, sys_argv)
    ini_file = 'hpir.ini'
    args = args_from_ini_file(ini_file, sys_argv)

    return src.hpcomm.HpComm().looper(args)


if __name__ == '__main__':
    run_main(sys.argv)
