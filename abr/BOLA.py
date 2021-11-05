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



import numpy as np
import math

class BOLA():
    def __init__(self, videoInfo, agent, log_file_path = None, *kw, **kws):
        self._videoInfo = videoInfo
        self._vms = None
        self._agent = None
        self.__init(agent)
    
    def __init(self, agent):
        SM = float(self._videoInfo.bitrates[-1])
        self._vms = [math.log(sm/SM) for sm in self._videoInfo.bitrates]
        self._agent = agent

    def getNextDownloadTime(self, *kw, **kws):
        V = 0.93
        lambdaP = 5 # 13
        sleepTime = 0
        agent = self._agent
        if len(agent._vRequests) == 0:
            return 0, 0
        buflen = agent._vBufferUpto - agent._vPlaybacktime
        if (agent._vMaxPlayerBufferLen - self._videoInfo.segmentDuration) <= buflen:
            sleepTime = buflen + self._videoInfo.segmentDuration - agent._vMaxPlayerBufferLen

        p = self._videoInfo.segmentDuration
        SM = float(self._videoInfo.bitrates[-1])
        lastM = agent._vRequests[-1].qualityIndex #last bitrateindex
        Q = buflen/p
        Qmax = self._agent._vMaxPlayerBufferLen/p
        ts = agent._vPlaybacktime - agent._vStartingPlaybackTime
        te = self._videoInfo.duration - agent._vPlaybacktime
        t = min(ts, te)
        tp = max(t/2, 3 * p)
        QDmax = min(Qmax, tp/p)

        VD = (QDmax - 1)/(self._vms[0] + lambdaP)

        M = np.argmax([((VD * self._vms[m] + VD*lambdaP - Q)/sm) \
                for m,sm in enumerate(self._videoInfo.bitrates)])
        if M < lastM:
            r = agent._vRequests[-1].throughput #throughput
            mp = min([m for m,sm in enumerate(self._videoInfo.bitrates) if sm/p < max(r, SM)] + [len(self._videoInfo.bitrates)])
            mp = 0 if mp >= len(self._videoInfo.bitrates) else mp
            if mp <= M:
                mp = M
            elif mp > lastM:
                mp = lastM
            elif False: #some special parameter TODO
                pass
            else:
                mp = mp - 1
            M = mp
        sleepTime = max(p * (Q - QDmax + 1), 0)
        return sleepTime, M

