#  Copyright 2008-2015 Nokia Networks
#  Copyright 2016-     Robot Framework Foundation
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




# --------------------------- 13/12/2016-----------------------------------
# slm5cob : Instead of assigning a StringIO object to _stream and redirecting
#           all the elements from pipe of sys.stdout, a new class ThreadPrinter
#           is created, which maintains different string buffers for print
#			statements of different threads.
#			These string buffers will be given to the corresponding Logger
#			objects when required, and flushed immediately.
# -------------------------------------------------------------------------

# --------------------------- 03/01/2017-----------------------------------
# slm5cob : New variables, 1) originalStream, 2) running_threads[] 
#           3) is_original_set are created in order to store the sys.stdout
#           object, before redirecting it to ThreadPrinter object.
#           Once all the threads move out of RTFW control, then the  
#           originalStream object is assigned back to the sys.stdout 
# -------------------------------------------------------------------------



import sys
from robot.utils import StringIO

from robot.output import new_logger_for_thread
from robot.utils import console_decode, console_encode, JYTHON

import threading
global originalStream
global running_threads
running_threads = []
global is_original_set
is_originalStream_set = 0
global _stream

class ThreadPrinter:
    def __init__(self):
        self.fhs = {}
    def write(self, value):
        f = self.fhs.get(threading.current_thread(),self.give_me_a_string())
        f = f+str(value)
        self.fhs[threading.current_thread()] = f
        

    def give_me_a_string(self):		
        if threading.current_thread() in self.fhs.keys():
            return self.fhs[threading.current_thread()]
        else:
            new_string = ""
            self.fhs[threading.current_thread()] = new_string
            return self.fhs[threading.current_thread()]
    def	give_me_the_msg(self):
        try:
            temp_string = self.fhs[threading.current_thread()]
            self.fhs[threading.current_thread()] = ""
            return temp_string
        except:
            never_mind = 1

_stream = ThreadPrinter()

class OutputCapturer(object):

    def __init__(self, library_import=False):
        self._library_import = library_import
        self._set_originalStream()
        self._python_out = PythonCapturer(stdout=True)
        sys.stdout = _stream
        self._python_err = PythonCapturer(stdout=False)
        #self._java_out = JavaCapturer(stdout=True)
        #self._java_err = JavaCapturer(stdout=False)
		
    def _set_originalStream(self):
        global is_originalStream_set
        global originalStream
        if is_originalStream_set == 0:
            originalStream = sys.stdout
            is_originalStream_set = 1

    def __enter__(self):
        if self._library_import:
            new_logger_for_thread().enable_library_import_logging()
        return self

    def __exit__(self, exc_type, exc_value, exc_trace):
        self._release_and_log()
        if self._library_import:
            new_logger_for_thread().disable_library_import_logging()
        return False

    def _release_and_log(self):
        stdout, stderr = self._release()
        if stdout:
            new_logger_for_thread().log_output(stdout)
        if stderr:
            new_logger_for_thread().log_output(stderr)
            sys.__stderr__.write(console_encode(stderr, stream=sys.__stderr__))

    def _release(self):
        #stdout = self._python_out.release() + self._java_out.release()
        #stderr = self._python_err.release() + self._java_err.release()
        #stdout = self._python_out.release() + self._java_out.release()
        global originalStream
        global running_threads
        running_threads.remove(threading.current_thread())
        if len(running_threads) is 0:
            sys.stdout = originalStream
        stdout = _stream.give_me_the_msg()
        #stderr = self._python_err.release() + self._java_err.release()
        stderr = _stream.give_me_the_msg()
        return stdout, stderr


class PythonCapturer(object):

    def __init__(self, stdout=True):
        global running_threads
        if stdout:
            self._original = sys.stdout
            running_threads.append(threading.current_thread())
            self._set_stream = self._set_stdout
        else:
            self._original = sys.stderr
            self._set_stream = self._set_stderr
        global _stream
        #self._stream = StringIO()
        #self._set_stream(self._stream)

    def _set_stdout(self, stream):
        sys.stdout = stream

    def _set_stderr(self, stream):
        sys.stderr = stream

    def release(self):
        # Original stream must be restored before closing the current
        self._set_stream(self._original)
        try:
            #return self._get_value(self._stream)
            never_mind = 1
        finally:
            #self._stream.close()
            #self._avoid_at_exit_errors(self._stream)
            never_mind = 1

    def _get_value(self, stream):
        try:
            return console_decode(stream.getvalue())
        except UnicodeError:
            # Error occurs if non-ASCII chars logged both as str and unicode.
            stream.buf = console_decode(stream.buf)
            stream.buflist = [console_decode(item) for item in stream.buflist]
            return stream.getvalue()

    def _avoid_at_exit_errors(self, stream):
        # Avoid ValueError at program exit when logging module tries to call
        # methods of streams it has intercepted that are already closed.
        # Which methods are called, and does logging silence possible errors,
        # depends on Python/Jython version. For related discussion see
        # http://bugs.python.org/issue6333
        stream.write = lambda s: None
        stream.flush = lambda: None


if not JYTHON:

    class JavaCapturer(object):

        def __init__(self, stdout=True):
            pass

        def release(self):
            return u''

else:

    from java.io import ByteArrayOutputStream, PrintStream
    from java.lang import System

    class JavaCapturer(object):

        def __init__(self, stdout=True):
            if stdout:
                self._original = System.out
                self._set_stream = System.setOut
            else:
                self._original = System.err
                self._set_stream = System.setErr
            self._bytes = ByteArrayOutputStream()
            self._stream = PrintStream(self._bytes, False, 'UTF-8')
            self._set_stream(self._stream)

        def release(self):
            # Original stream must be restored before closing the current
            self._set_stream(self._original)
            self._stream.close()
            output = self._bytes.toString('UTF-8')
            self._bytes.reset()
            return output
