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



import os
from util.myprint import myprint
import math
import json
import matplotlib.pyplot as plt
import numpy as np
import glob

from simenv.Simple import Simple, np, Simulator, load_trace, video, P2PNetwork
from util.group import GroupManager
import util.randStateInit as randstate
from util.easyPlotViewer import EasyPlot
from util.calculateMetric import measureQoE

# from rnnTimeout import getPensiveLearner, saveLearner
# import rnnAgent
# import rnnQuality


GROUP_JOIN_THRESHOLD = 10
BYTES_IN_MB = 1000000.0

LOG_LOCATION = "./results/"
def default(o):
    if isinstance(o, np.int64): return int(o)
    raise TypeError

class FLiDASH(Simple):
    def __init__(self, vi, traces, simulator, abr = None, grp = None, peerId = None, modelPath=None, *kw, **kws):
        super().__init__(vi=vi, traces=traces, simulator=simulator, abr=abr, peerId=peerId, *kw, **kws)
        self._vDownloadPending = False
#         self._vDownloadPendingRnnkey = None
#         self._vSegmentDownloading = -1
        self._vGroup = grp
        self._vCatched = {}
#         self._vOtherPeerRequest = {}
        self._vTotalDownloaded = 0
        self._vTotalUploaded = 0
        self._vTotalUploadedSegs = 0
        self._vStarted = False
        self._vFinished = False
        self._vModelPath = modelPath
        self._vRunWhenDownloadCompeltes = []

        self._vGroupNodes = None

        self._vGroupSegDetails = []

        self._vEarlyDownloaded = 0
        self._vNormalDownloaded = 0
        self._vThroughPutData = []
        self._vDownloadQueue = []
        self._vServingPeers = {}
        self._vDownloadedReqByItSelf = []
        self._vTimeoutDataAndDecision = {} # segId -> data
        self._vPlayBackDlCnt = 0
        self._vPlayerIdInGrp = -1
        self._vGroupStartedFromSegId = -1
        self._vImStarter = False
        self._vGroupStarted = False
        self._vNextGroupDownloader = -1
        self._vNextGroupDLSegId = -1
        self._vWeightedThroughput = 0
        self._vDownloadQl = []
        self._vMaxSegDownloading = -1
        self._vSyncNow = False
        self._vLastSyncSeg = -1
        self._vSleepingSegs = {}
        self._vSyncSegIds = set()

        self._vDeadLines = {}
        self._vDeadLineMissed = []
        #Loop debug
        self._vWaitedFor = {}
        self._vGrpIds = []

        self._vRPCCont = 0


#=============================================
    @property
    def groupId(self):
        return self._vGroup.getId(self)

#=============================================
    def start(self, startedAt = -1):
        super().start(startedAt)
        self._vAgent.addStartupCB(self.playerStartedCB)

#=============================================
    def playerStartedCB(self, *kw, **kwa):
        self._vStarted = True

#=============================================
    def die(self):
        self._vDead = True
        self._vGroup.remove(self, self._vAgent.nextSegmentIndex)

#=============================================
    def schedulesChanged(self, changedFrom, nodes, sched):
        newNodes = [x for x in nodes if x._vPlayerIdInGrp == -1]
        assert len(newNodes) == 1 #anything else is a disaster
        if newNodes[0] == self:
            self._vPlayerIdInGrp = len(nodes) - 1
        if newNodes[0] != self:
            if len(nodes) == 2:
                self.requestRpc(newNodes[0]._rGroupStarted)
        self._vGroupNodes = nodes
        self._vGrpIds = [n.networkId for n in nodes]
        syncTime = self.now + 1
        self._vSimulator.runAt(syncTime, self._rSyncNow)

#=============================================
    def _rGroupStarted(self):
        assert len(set([x._vPlayerIdInGrp for x in self._vGroupNodes])) == len(self._vGroupNodes)
        if len(self._vGroupNodes) == 2 and not self._vGroupStarted:
            self._vGroupStarted = self._vImStarter = True

#=============================================
    def _rGetRtt(self, node):
        return self._vGroup.getRtt(self, node)

#=============================================
    def _rTransmissionTime(self, *kw):
        return self._vGroup.transmissionTime(self, *kw)

#=============================================
    def _rSyncNow(self):
        self._vSyncNow = True

#=============================================
    def _rSyncComplete(self, segId):
        self._vSyncNow = False
        assert segId not in self._vCatched
        self._vLastSyncSeg = segId
        self._vSyncSegIds.add(segId)

#=============================================
    def _rFetchCompletePacket(self, req):
        cacheReq = self._vCatched[req.segId]
        if cacheReq != req and cacheReq.isComplete:
            self._vAgent._rBufManAddCompleteReq(cacheReq)
            return

        assert req.downloader != self
        assert req.downloader in self._vGroupNodes #Here i found a interesting result. There are certain time when we have better qualityIndex than orig req.

        self.requestRpc(req.downloader._rSendOrigReq, req, self, len(self._vGroupNodes))

#=============================================
    def _rSendOrigReq(self, req, remote, depth):
        if os.environ.get("EXPERIMENT_ENVIRON_RTT", None):
            if remote == self and self._vCatched[req.segId].isComplete: #very special case Just needed to get for the paper
                remote._rRecvOrigReq(self._vCatched[req.segId], self)
                return
        assert remote != self
        assert depth
        if self._vCatched[req.segId].downloader != self:
            self.requestRpc(self._vCatched[req.segId].downloader._rSendOrigReq, req, remote, depth-1)
            return

        assert req.segId in self._vCatched and self._vCatched[req.segId].isComplete
        reqOrig = self._vCatched[req.segId]
        assert reqOrig.isComplete
        if reqOrig.isComplete:
            self._vTotalUploaded += reqOrig.clen
            self._vTotalUploadedSegs += 1
        self.requestLongRpc(remote._rRecvOrigReq, reqOrig.clen, reqOrig, self)

#=============================================
    def _rRecvOrigReq(self, req, node):
        if req.segId in self._vSyncSegIds:
            req.syncSeg = True
        self._vAgent._rBufManAddCompleteReq(req)

#=============================================
    def requestRpc(self, func, *argv, **kargv):
        node = func.__self__
        assert node != self
        delay = self._rGetRtt(node)
        self._vRPCCont += 1
        self.runAfter(delay, node.recvRPC, func, self, *argv, **kargv)

#=============================================
    def requestLongRpc(self, func, clen, *argv, **kargv):
        node = func.__self__
        assert node != self
        delay = self._rTransmissionTime(node, clen)
        self.runAfter(delay, node.recvRPC, func, self, *argv, **kargv)

#=============================================
    def recvRPC(self, func, node, *argv, **kargv):
        s = func.__self__
        assert s == self and node.__class__ == self.__class__
        func(*argv, **kargv)

#=============================================
    def gossipSend(self, func, *argv, **kargv):
        strfunc = func.__name__
        for node in self._vGroupNodes:
            if node == self:
                continue
            self.requestRpc(node.gossipRcv, strfunc, *argv, **kargv)

#=============================================
    def gossipRcv(self, strfunc, *argv, **kargv):
        func = self.__getattribute__(strfunc)
        func(*argv, **kargv)

#=============================================
    def _rGetMyQuality(self, nextQl, segId, rnnkey):
        _, lastPlayerId, lastQl = list(zip(*([(0,0,0), (0,0,0)] + self._vGroupSegDetails[-5:])))

        lastPlayerId = [0]*5 + list(lastPlayerId)
        lastQl = [0]*5 + [x[1] for x in self._vDownloadQl[-5:]]

        deadLine = segId*self._vVideoInfo.segmentDuration - max([n._vAgent.playbackTime for n in self._vGroupNodes])
        curProg = self._rDownloadStatus()
        prog = len(self._vDownloadQueue) * 100 + (curProg[1] / curProg[2] if curProg[2] else 0)

        targetQl = lastQl[-1] if len(lastQl) > 1 else self._vAgent._vQualitiesPlayed[-1]

        clens = [ql[segId] for ql in self._vVideoInfo.fileSizes]

        thrpt = self._vThroughPutData[-5:]
        if curProg[1] > 0 and curProg[0] > 0:
            thrpt += [(self.now, curProg[1] * 8 / curProg[0])]
        cur = [1/x for t, x in thrpt]  #harmonic average
        cur = len(cur)/sum(cur)

        thrpt = min(cur, thrpt[-1][1], self._vWeightedThroughput)

        timereq = 0
        if curProg[2] > 0:
            timereq += ((curProg[2] - curProg[1])*8/thrpt)

        for s, q, k, _ in self._vDownloadQueue:
            cl = self._vVideoInfo.fileSizes[q][s]
            timereq += cl*8/thrpt

        self._vDeadLines[segId] = self.now + deadLine
        realDeadLine = deadLine - timereq
        if realDeadLine <= 0: #it is emergency

            return 0

        times = [(realDeadLine - cl*8/thrpt, i) for i, cl in enumerate(clens)]
        times = [x for x in times if x[0] > 0]
        if len(times) == 0:
            return 0
        times.sort(key = lambda x:x[0])
        ql = times[0][1]

        if ql > targetQl:
            if len(lastQl) >= 4 and min(lastQl[-4:]) == max(lastQl[-4:]):
                return targetQl + 1
            return targetQl

        if ql <= targetQl:
            return ql

        if nextQl > -1:
            return nextQl
        return 0

#=============================================
    def _rPenaltyDegradeTime(self, time, penalty):
        tsp = self.now - time
        PENALTY_ELIVATION_RATE = 1.5
        assert tsp >= 0
        penalty = time - penalty
        penalty -= PENALTY_ELIVATION_RATE*tsp
        return max(penalty, 0)

#=============================================
    def _rGetNextDownloader(self, segId):
        idleTimes = [ 0 if n._vDownloadPending else self.now - n._vWorkingTimes[-1][0]
                        for n in self._vGroupNodes]
        idleTimes = np.array(idleTimes)

        qlen = [len(n._vDownloadQueue) + (n==self) for n in self._vGroupNodes]
        qlen = np.array(qlen) * 100

        prog = [n._rDownloadStatus() for n in self._vGroupNodes]
        prog = [0 if x[2] == 0 else 100 - float(x[1])*100/float(x[2]) for x in prog]
        prog = np.array(prog)

        deadLinePenalty = np.array([0 if len(n._vDeadLineMissed)==0 else self._rPenaltyDegradeTime(*n._vDeadLineMissed[-1]) for n in self._vGroupNodes])

        res = idleTimes - qlen - prog - deadLinePenalty

        return np.argmax(res), None

        penalty = 0
        if nextPlayer >= len(self._vGroupNodes):
            penalty = 1000
            nextPlayer = np.random.randint(len(self._vGroupNodes))

        return nextPlayer, (rnnkey, penalty)

#=============================================
    def _rSetNextDownloader(self, playerId, segId, rnnkey, lastSegId, lastPlayerId, lastQl):
        infKey = (self.networkId, playerId, segId, rnnkey, lastPlayerId, lastQl)
        if not self._vGroupStarted:
            self._vGroupStarted = True
            self._vGroupStartedFromSegId = segId

        if playerId != self._vPlayerIdInGrp:
            self._vNextGroupDownloader = playerId
            self._vNextGroupDLSegId = segId
            self._vGroupSegDetails.append((lastSegId, lastPlayerId, lastQl))

            return #ignore the msg

        if segId >= self._vVideoInfo.segmentCount: #endof video
            return

        waitTime = self._vAgent._rIsAvailable(segId)
        if waitTime > 0:
            self._vWaitedFor.setdefault(segId, []).append((self.now, waitTime, "loc1"))
            self.runAfter(waitTime, self._rSetNextDownloader, playerId, segId, rnnkey, lastSegId, lastPlayerId, lastQl)
            return
        if self._vDownloadPending:
            self._vRunWhenDownloadCompeltes.append((self._rSetNextDownloader, [playerId, segId, rnnkey, lastSegId, lastPlayerId, lastQl], {}))
            assert len(self._vRunWhenDownloadCompeltes) < 10
            return

        syncSeg = False
        if self._vSyncNow:
            segId = max([n._vMaxSegDownloading + 1 for n in self._vGroupNodes] + [segId])
            self.gossipSend(self._rSyncComplete, segId)
            self._rSyncComplete(segId)
            syncSeg = True
            self._rSetNextDownloader(playerId, segId, rnnkey, lastSegId, lastPlayerId, lastQl)
            return
        elif segId == self._vLastSyncSeg or segId in self._vSyncSegIds:
            syncSeg = True
        elif self._vAgent.nextSegmentIndex > self._vLastSyncSeg:
            #check if there are bufferAvailable in player. This is wrong.
            waitTimes = []
            segPlaybackTime = self._vVideoInfo.segmentDuration*segId
            for node in self._vGroupNodes:
                if not node._vGroupStarted: continue
                curPlaybackTime = node._vAgent.playbackTime
                waitTime = max(0, segPlaybackTime - curPlaybackTime - node._vAgent._vMaxPlayerBufferLen + self._vVideoInfo.segmentDuration)
                waitTimes += [waitTime]
            waitTime = max(waitTimes)
            if waitTime > 0:
#                 assert waitTime < 100
                tmp = self._vWaitedFor.setdefault(segId, []).append((self.now, waitTime, "loc2"))
                self.runAfter(waitTime, self._rSetNextDownloader, playerId, segId, rnnkey, lastSegId, lastPlayerId, lastQl)
                return
#         elif

        self._vNextGroupDownloader = playerId
        self._vNextGroupDLSegId = segId
        self._vGroupSegDetails.append((lastSegId, lastPlayerId, lastQl))

        self._rDownloadAsTeamPlayer(segId, rnnkey = rnnkey, syncSeg = syncSeg, ql=lastQl)

#=============================================
    def _rDownloadAsTeamPlayer(self, segId, rnnkey = None, ql = -1, syncSeg = False):
        nextDownloader, rnnkey = self._rGetNextDownloader(segId)
        self._rAddToDownloadQueue(segId, ql, rnnkey=rnnkey, syncSeg=syncSeg)
        self.gossipSend(self._rSetNextDownloader, nextDownloader, segId+1, rnnkey, segId, self._vPlayerIdInGrp, ql)
        self._rSetNextDownloader(nextDownloader, segId + 1, rnnkey, segId, self._vPlayerIdInGrp, ql)

#=============================================
    def _rPredictedThroughput(self):
        #as per rate based algo
        thrpt = [1/x for t, x in self._vThroughPutData[-5:]]
        return len(thrpt)/sum(thrpt)

#=============================================
    def _rAddToDownloadQueue(self, nextSegId, nextQuality, position=float("inf"), sleepTime = 0, rnnkey = None, syncSeg = False):
        if sleepTime > 0:
            self.runAfter(sleepTime, self._rAddToDownloadQueue, nextSegId, nextQuality, position, 0, rnnkey, syncSeg)
            return
        found = False
        for s, q, k, _ in self._vDownloadQueue:
            if s == nextSegId and q == nextQuality:
                found = True
        position = min(position, len(self._vDownloadQueue))
        if not found:
            if self._vMaxSegDownloading < nextSegId:
                self._vMaxSegDownloading = nextSegId
            self._vDownloadQueue.insert(position, (nextSegId, nextQuality, rnnkey, syncSeg))
        self._rDownloadFromDownloadQueue()

#=============================================
    def _rDownloadingUsing(self, segId, ql):
        self._vDownloadQl.append((segId, ql))
        self._vDownloadQl.sort(key = lambda x : x[0])

#=============================================
    def _rDownloadFromDownloadQueue(self):
        if self._vDownloadPending:
            return
        while len(self._vDownloadQueue):
            segId, ql, rnnkey, syncSeg = self._vDownloadQueue.pop(0)
            if segId < self._vAgent.nextSegmentIndex: #we are not going to playit anyway.
                continue
            if segId >= self._vGroupStartedFromSegId and self._vGroupStarted:
                ql = self._rGetMyQuality(ql, segId, rnnkey)
                assert ql < len(self._vVideoInfo.fileSizes)
                self.gossipSend(self._rDownloadingUsing, segId, ql)
                self._rDownloadingUsing(segId, ql)

            self._rFetchSegment(segId, ql, extraData={"syncSeg":syncSeg})
            self._vDownloadPending = True
#             self._vDownloadPendingRnnkey = rnnkey
            break

#=============================================
    def _rDeadlineReached(self, segId):
        if segId in self._vCatched or segId < self._vAgent.nextSegmentIndex or segId < self._vLastSyncSeg:
            return
        _, lastPlayerId, lastQl = list(zip(*([(0,0,0), (0,0,0)] + self._vGroupSegDetails[-5:])))

        lastPlayerId = list(lastPlayerId)
        lastQl = list(lastQl)

        syncSeg = self._vLastSyncSeg == segId
        ql = max(min(lastQl), lastQl[-1])
        self._rAddToDownloadQueue(segId, ql, position=0, syncSeg=syncSeg)

#=============================================
    def _rDownloadNextData(self, nextSegId, nextQuality, sleepTime):
        if sleepTime > 0:
            self._vSleepingSegs[nextSegId] = self.now
            self.runAfter(sleepTime, self._rDownloadNextData, nextSegId, nextQuality, 0)
            return

        if nextSegId in self._vSleepingSegs:
            del self._vSleepingSegs[nextSegId]

        if nextSegId in self._vCatched:
            waitTime = max(self._vAgent._vMaxPlayerBufferLen - self._vAgent.bufferLeft, 0)
#             if waitTime >
            self._rAddToAgentBuffer(self._vCatched[nextSegId])
            return

        if not self._vGroupStarted or self._vGroupStartedFromSegId > nextSegId:
            self._rAddToDownloadQueue(nextSegId, nextQuality, sleepTime=sleepTime)
            return

        if self._vImStarter:
            self._vImStarter = False
            self._vGroupStarted = True
            self._vGroupStartedFromSegId = nextSegId
            self._rDownloadAsTeamPlayer(nextSegId, ql = nextQuality)
            return

        deadLine = (nextSegId-1) * self._vVideoInfo.segmentDuration - min([x._vAgent.playbackTime for x in self._vGroupNodes if x._vGroupStarted])
        if deadLine > 0:
            self.runAfter(deadLine, self._rDeadlineReached, nextSegId)
        else:
            self._rDeadlineReached(nextSegId)

#=============================================
    def _rAddToAgentBuffer(self, req, simIds=None):
        if req.segId in self._vSyncSegIds:
            req.syncSeg = True
        if self._vAgent.nextSegmentIndex > req.segId:
            return
        assert self._vAgent.nextSegmentIndex == req.segId or req.syncSeg
        if self._vAgent.nextSegmentIndex == req.segId:
            if os.environ.get("EXPERIMENT_ENVIRON_RTT", None):
                if req.segId in self._vCatched and (round(self._vAgent._vMaxPlayerBufferLen - self._vAgent.bufferLeft, 3) < self._vVideoInfo.segmentDuration and not req.syncSeg):
                    wait = self._vVideoInfo.segmentDuration - (self._vAgent._vMaxPlayerBufferLen - self._vAgent.bufferLeft)
                    self.runAfter(wait, self._rAddToAgentBuffer, req)
                    return
            assert req.segId in self._vCatched and (round(self._vAgent._vMaxPlayerBufferLen - self._vAgent.bufferLeft, 3) >= self._vVideoInfo.segmentDuration or req.syncSeg)

        waitTime = self._vAgent.bufferAvailableIn()
        assert waitTime <= 0 or req.syncSeg
        playableIn = req.segId * self._vVideoInfo.segmentDuration + self._vAgent._vGlobalStartedAt - (self._vAgent.bufferLeft * ( 1 - req.syncSeg)) - self.now
        if playableIn > 0:
            self.runAfter(playableIn, self._rAddToAgentBuffer, req, 0)
            return
        lastStalls = self._vAgent._vTotalStallTime
        self._vAgent._rAddToBufferInternal(req)

#=============================================
    def _rAddToBuffer(self, req, simIds = None):
        if req.segId in self._vSyncSegIds:
            req.syncSeg = True
        self._vDownloadPending = False
#         rnnkey = self._vDownloadPendingRnnkey
        self._rDownloadFromDownloadQueue()
        req.syncSeg = req.extraData.get("syncSeg", False)
        if self._vStarted:
            self._vPlayBackDlCnt += 1
        self._vThroughPutData += [(self.now, req.throughput)]
        self._vWeightedThroughput = 0.8*self._vWeightedThroughput + 0.2*req.throughput if self._vWeightedThroughput else req.throughput
        self._vDownloadedReqByItSelf += [req]

        if req.segId in self._vDeadLines:
            self._vDeadLineMissed.append((self.now, self._vDeadLines[req.segId]))
            del self._vDeadLines[req.segId]
        calls = self._vRunWhenDownloadCompeltes
        self._vRunWhenDownloadCompeltes = []
        for func, arg, kwarg in calls:
            func(*arg, **kwarg)

        syncSeg = req.syncSeg
        self._vTotalDownloaded += req.clen #i.e. peer download
        if req.segId in self._vCatched:
            syncSeg = syncSeg or self._vCatched[req.segId].syncSeg
        if req.segId not in self._vCatched \
                or req.qualityIndex > self._vCatched[req.segId].qualityIndex:
            self._vCatched[req.segId] = req
        self._vCatched[req.segId].syncSeg = syncSeg
        if (self._vAgent.nextSegmentIndex == req.segId and req.segId not in self._vSleepingSegs):
            self._rAddToAgentBuffer(self._vCatched[req.segId])
        elif syncSeg:
            self._rPushSyncSegInTime(req)

        if self._vPlayBackDlCnt == GROUP_JOIN_THRESHOLD:
            self._vConnectionSpeed = self._rPredictedThroughput()/1000000
            self._vGroup.add(self, self._vAgent.nextSegmentIndex+2)

        if self._vGroupNodes:
            self.gossipSend(self._rRecvReq, self, req.getIncompleteCopy())

#=============================================
    def _rPushSyncSegInTime(self, req):
        startTime = self._vAgent._vGlobalStartedAt + self._vVideoInfo.segmentDuration * req.segId
        waitTime = max(0, startTime - self.now)
        if waitTime > 0:
            self.runAfter(waitTime, self._rPushSyncSegInTime, req)
            return
        self._rAddToAgentBuffer(self._vCatched[req.segId])

#=============================================
    def _rRecvReq(self, node, req):
        syncSeg = req.syncSeg
        if self._vWorking:
            _, _, dlSeg, _, downloadData, _, _ = self._vWorkingStatus
            if dlSeg == req.segId:
                self._rStopDownload()
        if req.segId in self._vCatched:
            syncSeg = syncSeg or self._vCatched[req.segId].syncSeg
        if req.segId not in self._vCatched \
                or req.qualityIndex > self._vCatched[req.segId].qualityIndex:
            if req.isComplete:
                node._vTotalUploaded += req.clen
                node._vTotalUploadedSegs += 1
            self._vCatched[req.segId] = req
        self._vCatched[req.segId].syncSeg = syncSeg

        if (self._vAgent.nextSegmentIndex == req.segId and req.segId not in self._vSleepingSegs):
            self._rAddToAgentBuffer(self._vCatched[req.segId])
        elif syncSeg:
            self._rPushSyncSegInTime(req)

#=============================================
#=============================================
#=============================================
AGENT_TRACE_MAP = {}
def plotIdleStallTIme(dpath, group):
    if not os.path.isdir(dpath):
        os.makedirs(dpath)

    colors = ["blue", "green", "red", "cyan", "magenta", "yellow", "black"]

    pltHtmlPath = os.path.join(dpath,"groupP2PTimeout.html")
    open(pltHtmlPath, "w").close()
    eplt = EasyPlot()
    for ql,grpSet in group.groups.items():
        for grp in grpSet:
            grpLabel = str([x._vPeerId for x in grp.getAllNode()])
            label = "<hr><h2>BufferLen</h2>"
            label += " NumNode:" + str(len(grp.getAllNode()))
            label += " Quality Index: " + str(grp.qualityLevel)
            eplt.addFig()
            for i, ag in enumerate(grp.getAllNode()):
                pltData = ag._vAgent._vBufferLenOverTime
                Xs, Ys = list(zip(*pltData))
                eplt.plot(Xs, Ys, marker="x", label=str(ag._vPeerId), color=colors[i%len(colors)])

                label += "\n<br><span style=\"color: " + colors[i%len(colors)] + "\" >PeerId: " + str(ag._vPeerId)
                label += " avgQualityIndex: " + str(ag._vAgent.avgQualityIndex)
                label += " avgStallTime: " + str(ag._vAgent.totalStallTime)
                label += " startedAt: " + str(ag._vAgent._vStartedAt)
                label += " traceIdx: " + str(AGENT_TRACE_MAP.get(ag._vPeerId, 0))
                label += "</span>"
            eplt.setFigHeader(label)
            label = "<h2>workingTime</h2>"
            eplt.addFig()
            for i, ag in enumerate(grp.getAllNode()):
                pltData = ag._vWorkingTimes
                Xs, Ys, Zs = list(zip(*pltData))
                eplt.step(Xs, Ys, toolTipData=Zs, marker="o", label="idleTime", where="pre", color=colors[i%len(colors)])
            eplt.setFigHeader(label)
            label = "<h2>StallTime</h2>"
            eplt.addFig()
            for i, ag in enumerate(grp.getAllNode()):
                pltData = ag._vAgent._vTimeSlipage
                Xs, Ys, Zs = list(zip(*pltData))
                eplt.plot(Xs, Ys, toolTipData=Zs, marker="o", label="idleTime", where="pre", color=colors[i%len(colors)])
            eplt.setFigHeader(label)

            label = "<h2>qualityLevel</h2>"
            eplt.addFig()
            for i, ag in enumerate(grp.getAllNode()):
                pltData = ag._vAgent._vQualitiesPlayedOverTime
                Xs, Ys, Zs = list(zip(*pltData))
                eplt.step(Xs, Ys, toolTipData=Zs, marker="o", label="idleTime", where="post", color=colors[i%len(colors)])
            eplt.setFigHeader(label)

    with open(pltHtmlPath, "w") as fp:
        eplt.printFigs(fp, width=1000, height=400)

#=============================================
def experimentGroupP2PBig(traces, vi, network):
    randstate.loadCurrentState()
    simulator = Simulator()
    grp = GroupManager(4, len(vi.bitrates)-1, vi, network)#np.random.randint(len(vi.bitrates)))

    deadAgents = []
    ags = []
    maxTime = 0
    startsAts= np.random.randint(5, vi.duration/2, size=network.numNodes())
    trx = np.random.randint(len(traces), size=network.numNodes())
    for x, nodeId in enumerate(network.nodes()):
        idx = trx[x]
        startsAt = startsAts[x]
        trace = traces[idx]
        env = FLiDASH(vi, trace, simulator, None, grp, nodeId)
        simulator.runAt(startsAt, env.start, 5)
        maxTime = 101.0 + x
        AGENT_TRACE_MAP[nodeId] = idx
        ags.append(env)
    simulator.run()
    grp.printGroupBucket()
    for i,a in enumerate(ags):
        assert a._vFinished # or a._vDead
    if __name__ == "__main__":
        plotIdleStallTIme("results/stall-idle/", grp)
    return ags

def experimentGroupP2PSmall(traces, vi, network):
    simulator = Simulator()
    grp = GroupManager(4, len(vi.bitrates)-1, vi, network)#np.random.randint(len(vi.bitrates)))

    deadAgents = []
    ags = []

    for trx, nodeId, startedAt in [( 5, 267, 107), (36, 701, 111), (35, 1800, 124), (5, 2033, 127)]:
        trace = traces[trx]
        env = FLiDASH(vi, trace, simulator, None, grp, nodeId)
        simulator.runAt(startedAt, env.start, 5)
        AGENT_TRACE_MAP[nodeId] = trx
        ags.append(env)

    simulator.run()
    grp.printGroupBucket()
    for i,a in enumerate(ags):
        assert a._vFinished # or a._vDead
    if __name__ == "__main__":
        plotIdleStallTIme("results/stall-idle/", grp)
    return ags

def main():
#     randstate.storeCurrentState() #comment this line to use same state as before
    for fpath in glob.glob("videofilesizes/*.py"):
#         randstate.storeCurrentState() #comment this line to use same state as before
        randstate.loadCurrentState()
        traces = load_trace.load_trace()
        vi = video.loadVideoTime("./videofilesizes/sizes_qBVThFwdYTc.py")
        vi = video.loadVideoTime("./videofilesizes/sizes_penseive.py")
        vi = video.loadVideoTime(fpath)
        vi = video.loadVideoTime("./videofilesizes/sizes_qBVThFwdYTc.py")
        assert len(traces[0]) == len(traces[1]) == len(traces[2])
        traces = list(zip(*traces))
        network = P2PNetwork("./p2p-Gnutella04.txt")
        network = P2PNetwork()

        experimentGroupP2PBig(traces, vi, network)
        return

if __name__ == "__main__":
    for x in range(3):
        main()
        print("=========================\n")
        break
