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
    def  __init__(self, fpath = "./graph/weighted.txt"):
        self.grp = nx.Graph()
        self.__readPfile(fpath)
        is_close_file_path = "C:\\Users\\sanket\\Desktop\\semester\\MTP_2\\is_close.txt"



        # self.is_close_number = int(open(is_close_file_path, "r").read())

        from statistics import median
        import math
        ################################ dia/2 ################################

        # self.is_close_number = math.ceil(nx.diameter(self.grp)/2) + 1
        ################################ dia/2 ################################

        ################################ Median of eccentricity ################################
        # e_dict = nx.eccentricity(self.grp)
        # temp = []
        # for i in e_dict:
        #     temp.append(e_dict[i])
        # self.is_close_number = math.ceil(median(temp)) + 1

        ################################ Median of eccentricity ################################

        ################################ Median of all possible dist ################################
        # nx.eccentricity(self.grp)
        # self.is_close_numbe = math.ceil(
        #     nx.average_shortest_path_length(self.grp)) + 1

        ################################ Median of all possible dist ################################

    def __readPfile(self, fpath):
        temp = []
        with open(fpath) as fp:
            for line in fp:
                if line[0] == "#":
                    continue
                n1, n2,w = [x for x in line.strip().split()]
                n1 = int(n1)
                n2 = int(n2)
                w = float(w)
                temp.append((n1,n2,w))
        self.grp.add_weighted_edges_from(temp)
        print(self.grp.adj)

    def nodes(self):
        nodes = sorted(self.grp.nodes())
        for node in nodes:
            yield node

    def numNodes(self):
        return len(self.grp.nodes())

    def getDistance(self, n1, n2):
        return nx.shortest_path_length(self.grp, source=n1, target=n2, weight='weight', method='dijkstra')

    def isClose(self, n1, n2):
#         return True
        dist = self.getDistance(n1, n2)
        # return dist < 3 #threshold
        return dist < self.is_close_number

    def getRtt(self, n1, n2):
        distance = self.getDistance(n1, n2)
        # distance = min(9, distance) # think this will be unnecceary in our case since we don't assume same weight
#         distance = max(2, distance)

        rtt = 2**distance
        # code #6 from  https://www.geeksforgeeks.org/python-os-environ-object/
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
