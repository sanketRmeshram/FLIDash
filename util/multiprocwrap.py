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



import util.multiproc as mp
import os
Pipe = mp.Pipe
Queue = mp.Queue

DEFAULT_STD_DIR = "stdouterrdir"

def Process(outPref=None, errPref=None, *argv, **kwargv):
    if not outPref and not errPref:
        if not os.path.isdir(DEFAULT_STD_DIR):
            os.makedirs(DEFAULT_STD_DIR)
        outPref = os.path.join(DEFAULT_STD_DIR, "out_" + str(os.getpid()))
        errPref = os.path.join(DEFAULT_STD_DIR, "err_" + str(os.getpid()))
    return mp.Process(outPref = outPref, errPref = errPref, *argv, **kwargv)
