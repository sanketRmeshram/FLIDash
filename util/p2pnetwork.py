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



import networkx as nx
import numpy as np
import os

class P2PNetwork():
    def  __init__(self, fpath = "./graph/as19990829.txt"):
        self.grp = nx.Graph()
        self.__readPfile(fpath)

    def __readPfile(self, fpath):
        with open(fpath) as fp:
            for line in fp:
                if line[0] == "#":
                    continue
                n1, n2 = [int(x) for x in line.strip().split()]
                self.grp.add_edge(n1, n2)

    def nodes(self):
        nodes = sorted(self.grp.nodes())
        for node in nodes:
            yield node

    def numNodes(self):
        return len(self.grp.nodes())

    def getDistance(self, n1, n2):
        return nx.shortest_path_length(self.grp, n1, n2)

    def isClose(self, n1, n2):
#         return True
        dist = self.getDistance(n1, n2)
        return dist < 3 #threshold

    def getRtt(self, n1, n2):
        distance = self.getDistance(n1, n2)
        distance = min(9, distance)
#         distance = max(2, distance)

        rtt = 2**distance
        extVar = int(os.environ.get("EXPERIMENT_ENVIRON_RTT", "-1"))
        if extVar > 0:
            rtt = extVar
        rtt *= np.random.uniform(0.95, 1.05)
        return rtt/1000.0

    def transmissionTime(self, n1, n2, size, buf=64*1024, maxSpeed=-1): #default 5mb data
        maxSpeed = max(maxSpeed, 40*1000*1000) if maxSpeed == -1 else maxSpeed
        rtt = self.getRtt(n1, n2)
        speed = buf * 8 / rtt
        speed = min(maxSpeed, speed)
        time = size*8/speed
        time *= np.random.uniform(0.95, 1.05)
        return time



def main():
    grp = Network()
    for node in grp.nodes():
        print(node)

if __name__ == "__main__":
    main()
