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



import json
import numpy as np

def defaultEncoder(o):
    if isinstance(o, np.int64): return int(o)
    raise TypeError


def dump(*arg, default=None, **kwarg):
    if not default:
        default=defaultEncoder
    return json.dump(*arg, default=default, **kwarg)

def dumps(*arg, default=None, **kwarg):
    if not default:
        default=defaultEncoder
    return json.dumps(*arg, default=default, **kwarg)

def loads(*arg, **kwarg):
    return json.loads(*arg, **kwarg)

def load(*arg, **kwarg):
    return json.load(*arg, **kwarg)

