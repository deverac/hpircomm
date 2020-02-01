import mock


# Derived from types.SimpleNamespace in Python 3.3
class TAttrBag:
    """
    An attribute-bag for use in testing.
    Returns an object containing the supplied attributes and values.
    bb = TAttrBag(height='tall', age=23)
    print bb.height  # prints 'tall'
    """
    def __init__(self, **kw):
        self.__dict__.update(kw)


    def __repr__(self):
        keys = sorted(self.__dict__)
        items = ("{}={!r}".format(k, self.__dict__[k]) for k in keys)
        typ = type(self).__name__
        if typ == 'instance':
            typ = self.__class__.__name__
        return "{}({})".format(typ, ", ".join(items))

    def __eq__(self, other):
        return self.__dict__ == other.__dict__



class sert:
    """
    Syntatic sugar for unittest.mock assertions.
    obj: A unittest.mock or a value.
    fn_name: A function name as a string.
    Specifying fn_name is only for convenience.
    sert(aa, 'bb') is the same as sert(aa.return_value.bb)
    """
    def __init__(self, obj, fn_name=None):
        if isinstance(obj, mock.mock.Mock):
            self.mock = obj
            if fn_name:
                self.mock = getattr(self.mock.return_value, fn_name)
        else:
            self.val = obj

    def called_once(self):
        self.mock.assert_called_once()

    def called_twice(self):
        assert len(self.mock.call_args_list) == 2

    def called_n_times(self, n):
        if len(self.mock.call_args_list) != n:
            raise Exception('Expected call count ({}) exceeded actual call count ({})'.format(n, len(self.mock.call_args_list)))

    def any_call(self, *args):
        self.mock.assert_any_call(*args)

    def not_called(self):
        self.mock.assert_not_called()

    def called_with(self, *args, **kwargs):
        self.mock.assert_called_with(*args, **kwargs)

    def called_once_with(self, *args, **kwargs):
        self.called_once()
        self.called_with(*args, **kwargs)

    def first_call_called_with(self, *args):
        self.nth_call_called_with(1, *args)

    def second_call_called_with(self, *args):
        self.nth_call_called_with(2, *args)

    def last_call_called_with(self, *args):
        self.called_with(*args)

    def nth_call_called_with(self, n, *args):
        if n < 1:
            raise Exception('Invalid call count ({})'.format(n))
        elif n-1 < len(self.mock.call_args_list):
            bak = self.mock.call_args
            self.mock.call_args = self.mock.call_args_list[n-1]
            self.mock.assert_called_with(*args)
            self.mock.call_args = bak
        else:
            raise Exception('Expected call count ({}) exceeded actual call count ({})'.format(n, len(self.mock.mock_calls)))

    def is_true(self):
        assert self.val == True

    def is_false(self):
        assert self.val == False

    def to_equal(self, v):
        if self.val != v:
            raise Exception('Expected {} to equal {}'.format(self.val, v))

    def not_equal(self, v):
        if self.val == v:
            raise Exception('Expected {} to not equal {}'.format(self.val, v))
