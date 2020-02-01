import logging

FORMAT = '%(prefix)s%(message)s'
logging.basicConfig(level=10, format=FORMAT)


class d:
    def __init__(self, msg, *args, **kwargs):
        kwargs['extra'] = {'prefix': ''}
        logging.debug(msg, *args, **kwargs) # Level 10


class i:
    def __init__(self, msg, *args, **kwargs):
        kwargs['extra'] = {'prefix': ''}
        logging.info(msg, *args, **kwargs) # Level 20


class w:
    def __init__(self, msg, *args, **kwargs):
        kwargs['extra'] = {'prefix': ''}
        logging.warning(msg, *args, **kwargs) # Level 30


class e:
    def __init__(self, msg, *args, **kwargs):
        kwargs['extra'] = {'prefix': 'ERROR: '}
        logging.error(msg, *args, **kwargs) # Level 40


class c:
    def __init__(self, msg, *args, **kwargs):
        kwargs['extra'] = {'prefix': ''}
        logging.critical(msg, *args, **kwargs) # Level 50


class set_log_level:
    def __init__(self, lvl):
        logging.disable(logging.NOTSET) # 0

        if lvl < 1:
            lvl = 1

        if lvl == 1:
            log_level = logging.CRITICAL + 10000000
        elif lvl == 2:
            log_level = logging.CRITICAL # 50
        elif lvl == 3:
            log_level = logging.ERROR # 40
        elif lvl == 4:
            log_level = logging.WARNING # 30
        elif lvl == 5:
            log_level = logging.INFO # 20
        else:
            log_level = logging.DEBUG # 10

        logging.getLogger().setLevel(log_level)


def get_log_level():
    level = logging.getLogger().getEffectiveLevel()
    if level > 60:
        return 1
    return (70 - level) / 10
