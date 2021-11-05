# * This is an implementation of FLiDASH.
# * Copyright (C) 2019  Abhijit Mondal
# *
# * This program is free software: you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation, either version 3 of the License, or
# * (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program.  If not, see <http://www.gnu.org/licenses/>.



import traceback as tb
import os
import sys



def getTraceBack(exc_info):
    error = "pid:" + str(os.getpid()) + " ppid:" + str(os.getppid()) + "\n"
    error += str(exc_info[0]) + "\n"
    error += str(exc_info[1]) + "\n\n"
    error += "\n".join(tb.format_tb(exc_info[2]))
    return error

def lineno():
    return sys._getframe().f_back.f_lineno

def getPosition():
    frame = sys._getframe().f_back
    line = frame.f_lineno
    fileName = frame.f_code.co_filename
    return f"{fileName}:{line}"

def getStack():
    frame = sys._getframe().f_back
    stack = []
    while frame:
        line = frame.f_lineno
        fileName = frame.f_code.co_filename
        func = frame.f_code.co_name
        st = f"{func} at {fileName}:{line}"
        stack += [st]
        frame = frame.f_back
    return stack
