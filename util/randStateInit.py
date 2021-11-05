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



import numpy
import pickle
import os

def storeCurrentState(fp = "/tmp/randstate"):
    state = numpy.random.get_state()
    with open(fp, "wb") as f:
        pickle.dump(state, f, pickle.HIGHEST_PROTOCOL)
        print("saved")

def loadCurrentState(fp = "/tmp/randstate"):
    if not os.path.exists(fp):
        return storeCurrentState(fp)
    with open(fp, "rb") as f:
        state = pickle.load(f)
        numpy.random.set_state(state)
        print("loaded")
