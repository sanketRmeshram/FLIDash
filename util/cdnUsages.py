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





class CDN():
    __instance = None
    @staticmethod
    def getInstance():
        if CDN.__instance == None:
            CDN()
        return CDN.__instance

    def __init__(self):
        assert CDN.__instance == None
        CDN.__instance = self
#         self.throughput = []
        self.totaldownloaded = 0
        self.points = []
        self._vThroughput = None
        self._vUploaded = None

    @staticmethod
    def clear():
        CDN.__instance = None

    def add(self, fromTimeSec, toTimeSec, bandwidthBps):
        self.addMili(round(fromTimeSec*1000), round(toTimeSec * 1000), bandwidthBps)

    @property
    def throughput(self):
        if self._vThroughput:
            return self._vThroughput
        self.points.sort(key=lambda x : x[0])
        self._vThroughput = []
        curBw = 0.0
        for t, bw, start in self.points:
            self._vThroughput.append((t, curBw))
            if start:
                curBw += bw
            else:
                curBw -= bw
            cbw = round(curBw, 3) #it is in bps
            assert cbw >= 0
            self._vThroughput.append((t, cbw))
        return self._vThroughput

    def throughputGran(self, scale=-1):
        if scale <= 0:
            return self.throughput
        cdnThr = self.throughput
        grnThr = []
        transferred = 0
        lastMark, nextMark = 0, scale

        lt, lbw = 0, 0
        for i, elm in enumerate(self.throughput):
            t, bw = elm
            tdiff = t - lt
            bw = round(bw, 3)
            tdiff = round(tdiff, 3)
            assert tdiff >= 0 and bw >= 0
            dTrans = bw * tdiff/1000

            while t >= nextMark: #a precaution incase tdiff > scale
                dTrans = bw * (nextMark - lt) / 1000
                transferred += dTrans
                dbw = transferred*1000/scale
                grnThr += [(lastMark, dbw)]

                dTrans = bw * (t - nextMark) / 100
                lastMark = nextMark
                nextMark += scale
                transferred = 0

            transferred += dTrans


            lt, lbw = t, bw
        return grnThr

    @property
    def uploaded(self):
        if self._vUploaded:
            return self._vUploaded
        self._vUploaded = []
        lt, lbw = 0, 0
        uploaded = 0
        for i, elm in enumerate(self.throughput):
            t, bw = elm
            tdiff = t - lt
            assert tdiff >= 0
            if bw > 0 and tdiff > 0:
                self._vUploaded.append((t, int(uploaded)))
                uploaded += (bw * tdiff/1000/8) #bytes
                self._vUploaded.append((t, int(uploaded)))
            lt, lbw = t, bw

        return self._vUploaded


    @property
    def uploadRequests(self):
        upReqOverTime = [(0,0)]
        upReqCnt = 0
        for t, bw, start in self.points:
            if start:
                upReqCnt += 1
                upReqOverTime.append((t, upReqCnt))
        return upReqOverTime


    def addMili(self, fromTime, toTime, bandwidthBps):
        self.points.append((fromTime, bandwidthBps, True))
        self.points.append((toTime, bandwidthBps, False))
        self._vThroughput = None
        self._vUploaded = None



def main():
    p = CDN.getInstance()
    p.addMili(5, 9, 1)
    p.addMili(5, 9, 1)
    p.addMili(4, 8, 1)
    p.addMili(6, 10, 1)
    p.addMili(3, 12, 1)
    print(p.throughput)


if __name__ == "__main__":
    main()
