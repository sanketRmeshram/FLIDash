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



from simulator.priorityQueue import PriorityQueue
import random
import sys
import os

def getStack():
#     if os.environ.get("SIMULATOR_MODE", "").upper() != "DEBUG": return None
    frame = sys._getframe().f_back
    stack = []
    while frame:
        line = frame.f_lineno
        fileName = frame.f_code.co_filename
        func = frame.f_code.co_name
        st = f"{func}() at {fileName}:{line}\n"
        stack += [st]
        frame = frame.f_back
    return stack


class Simulator():
    def __init__(self):
        self.queue = PriorityQueue()
        self.now = 0.0
        self.taskRemoved = set()
        self.taskId = 0

    def runAfter(self, after, callback, *args, **kw):
        return self.runAt(self.now+after, callback, *args, **kw)

    def runAt(self, at, callback, *args, **kw):
        at = float(at)
        assert at >= self.now
        tskId = self.taskId
        self.taskId += 1
        stack = getStack()
        self.queue.insert(at, (at, tskId, stack, callback, args, kw))
        return tskId

    def getNow(self):
        return self.now

    def cancelTask(self, reference):
        assert reference not in self.taskRemoved
        self.taskRemoved.add(reference)
#         return self.queue.delete(reference)

    def run(self):
        while not self.queue.isEmpty():
            at, tskId, stack, callback, args, kw = self.queue.extractMin()
            if tskId in self.taskRemoved:
                self.taskRemoved.remove(tskId)
                continue
            self.now = at
            callback(*args, **kw)

    def isPending(self, ref):
        return self.queue.isRefExists(ref)

    def runNow(self, callback, *args, **kw):
        nexTime = self.now()

        return self.queue.insert(nexTime, (self.now, callback, args, kw))

def smtest(sm, cmd, x=-1):
    print(sm.getNow(), cmd, x)
    if cmd == "add":
        time = sm.getNow() + random.uniform(0, 9)
        sm.runAt(time, smtest, sm, "none")

if __name__ == "__main__":
    sm = Simulator()
    sm.runAt(0.25, smtest, sm, "add", 1)
    sm.runAt(5.25, smtest, sm, "add", 2)
    i = sm.runAt(3.25, smtest, sm, "add", 3)
    sm.runAt(4.25, smtest, sm, "add", 4)
    sm.runAt(6.25, smtest, sm, "add", 5)
    sm.runAt(7.25, smtest, sm, "add", 6)
    sm.runAt(2.25, smtest, sm, "add", 7)
    sm.runAt(3.0, sm.cancelTask, i)
    sm.runAt(3.0, sm.cancelTask, i+1)
    sm.run()


