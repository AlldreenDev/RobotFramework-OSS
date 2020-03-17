#  Copyright 2008-2015 Nokia Solutions and Networks
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from . import pyloggingconf
from .debugfile import DebugFile
from .listeners import LibraryListeners, Listeners
from .logger import *
from .loggerhelper import AbstractLogger
from .xmllogger import XmlLogger

class Output(AbstractLogger):

    def __init__(self, settings):
        AbstractLogger.__init__(self)
        self.logger = new_logger_for_thread()
        self._xmllogger = XmlLogger(settings.output, settings.log_level)
        self.listeners = Listeners(settings.listeners, settings.log_level)
        self.library_listeners = LibraryListeners(settings.log_level)
        self._register_loggers(DebugFile(settings.debug_file))
        self._settings = settings

    def _register_loggers(self, debug_file):
        self.logger.register_xml_logger(self._xmllogger)
        self.logger.register_listeners(self.listeners or None, self.library_listeners)
        if debug_file:
            self.logger.register_logger(debug_file)

    def register_error_listener(self, listener):
        self.logger.register_error_listener(listener)

    def close(self, result):
        self._xmllogger.visit_statistics(result.statistics)
        self._xmllogger.close()
        self.logger.unregister_xml_logger()
        self.logger.output_file('Output', self._settings['Output'])

    def start_suite(self, suite):
        self.logger.start_suite(suite)

    def end_suite(self, suite):
        self.logger.end_suite(suite)

    def start_test(self, test):
        self.logger.start_test(test)

    def end_test(self, test):
        self.logger.end_test(test)

    def start_keyword(self, kw):
        self.logger.start_keyword(kw)

    def end_keyword(self, kw):
        self.logger.end_keyword(kw)

    def message(self, msg):
        self.logger.log_message(msg)

    def set_log_level(self, level):
        pyloggingconf.set_level(level)
        self.listeners.set_log_level(level)
        self.library_listeners.set_log_level(level)
        return self._xmllogger.set_log_level(level)
