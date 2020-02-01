import readline
import sys
import traceback

import dispatcher
import log

EXIT_OK = 0
EXIT_ERR = 1


def read_history_file(filename):
    try:
        readline.read_history_file(filename)
    except IOError:
        pass


def write_history_file(filename):
    try:
        readline.write_history_file(filename)
    except IOError:
        pass



class HpComm:

    def looper(self, args):
        except_count = 0
        history_file = '.hpirhist'
        exit_val = EXIT_OK
        d = None

        try:
            log.set_log_level(args.log)
            read_history_file(history_file)

            d = dispatcher.Dispatcher(args)
            d.start_transport()

            while not d.is_done():
                try:
                    d.read_and_exec()
                    except_count = 0
                except:
                    except_count += 1
                    log.i('') # Ensure the following error message starts on a new line.
                    log.e('{} : {}'.format(sys.argv[0], sys.exc_info()[1]))
                    if d.is_trace_on_error():
                        print traceback.format_exc()
                    if (except_count >= 2) or d.is_exit_on_error():
                        exit_val = EXIT_ERR
                        d.force_done()

            write_history_file(history_file)
        except:
            exit_val = EXIT_ERR
            print traceback.format_exc()
        finally:
            if d:
                d.stop_transport()

        return exit_val
