import unittest
import logging

import src.log

from mock import mock, patch, Mock, MagicMock

from tests.sert import sert

LOG_DEBUG    = 10
LOG_INFO     = 20
LOG_WARNING  = 30
LOG_ERROR    = 40
LOG_CRITICAL = 50

SILENT = 10000050



class TestLogD(unittest.TestCase):

    @patch('src.log.logging')
    def test_should_log_debug(self, mock_log):
        src.log.d('a debug message')
        sert(mock_log.debug).called_once_with('a debug message', extra={'prefix': ''})



class TestLogI(unittest.TestCase):

    @patch('src.log.logging')
    def test_should_log_info(self, mock_log):
        src.log.i('an info message')
        sert(mock_log.info).called_once_with('an info message', extra={'prefix': ''})



class TestLogW(unittest.TestCase):

    @patch('src.log.logging')
    def test_should_log_warn(self, mock_log):
        src.log.w('a warning message')
        sert(mock_log.warning).called_once_with('a warning message', extra={'prefix': ''})



class TestLogE(unittest.TestCase):

    @patch('src.log.logging')
    def test_should_log_error(self, mock_log):
        src.log.e('an error message')
        sert(mock_log.error).called_once_with('an error message', extra={'prefix': 'ERROR: '})



class TestLogC(unittest.TestCase):

    @patch('src.log.logging')
    def test_should_log_critical(self, mock_log):
        src.log.c('a critical message')
        sert(mock_log.critical).called_once_with('a critical message', extra={'prefix': ''})



class TestSetLogLevel(unittest.TestCase):

    def tearDown(self):
        src.log.set_log_level(1) # Reset log level to suppress output


    @patch('logging.getLogger')
    def test_should_handle_negative(self, mock_log):
         src.log.set_log_level(-1)
         sert(mock_log, 'setLevel').called_with(SILENT)


    @patch('logging.getLogger')
    def test_should_handle_zero(self, mock_log):
         src.log.set_log_level(0)
         sert(mock_log, 'setLevel').called_with(SILENT)


    @patch('logging.getLogger')
    def test_should_set_silent(self, mock_log):
        src.log.set_log_level(1)
        sert(mock_log, 'setLevel').called_with(SILENT)


    @patch('logging.getLogger')
    def test_should_set_critical(self, mock_log):
        src.log.set_log_level(2)
        sert(mock_log, 'setLevel').called_with(LOG_CRITICAL)


    @patch('logging.getLogger')
    def test_should_set_error(self, mock_log):
        src.log.set_log_level(3)
        sert(mock_log, 'setLevel').called_with(LOG_ERROR)


    @patch('logging.getLogger')
    def test_should_set_warning(self, mock_log):
        src.log.set_log_level(4)
        sert(mock_log, 'setLevel').called_with(LOG_WARNING)


    @patch('logging.getLogger')
    def test_should_set_info(self, mock_log):
        src.log.set_log_level(5)
        sert(mock_log, 'setLevel').called_with(LOG_INFO)


    @patch('logging.getLogger')
    def test_should_set_debug(self, mock_log):
        src.log.set_log_level(6)
        sert(mock_log, 'setLevel').called_with(LOG_DEBUG)


    @patch('logging.getLogger')
    def test_should_handle_large_val(self, mock_log):
         src.log.set_log_level(99999)
         sert(mock_log, 'setLevel').called_with(LOG_DEBUG)



class TestGetLogLevel(unittest.TestCase):

    def tearDown(self):
        src.log.set_log_level(1) # Reset log level to suppress output


    def test_should_get_debug(self):
        logging.getLogger().setLevel(LOG_DEBUG)
        sert(src.log.get_log_level()).to_equal(6)


    def test_should_get_info(self):
        logging.getLogger().setLevel(LOG_INFO)
        sert(src.log.get_log_level()).to_equal(5)


    def test_should_get_warning(self):
        logging.getLogger().setLevel(LOG_WARNING)
        sert(src.log.get_log_level()).to_equal(4)


    def test_should_get_error(self):
        logging.getLogger().setLevel(LOG_ERROR)
        sert(src.log.get_log_level()).to_equal(3)


    def test_should_get_critical(self):
        logging.getLogger().setLevel(LOG_CRITICAL)
        sert(src.log.get_log_level()).to_equal(2)


    def test_should_get_large_num(self):
        logging.getLogger().setLevel(999999)
        sert(src.log.get_log_level()).to_equal(1)
