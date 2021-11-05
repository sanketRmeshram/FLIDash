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



REBUF_PENALTY = 4.3  # 1 sec rebuffering -> this number of Mbps
SMOOTH_PENALTY = 1
M_IN_K = 1000.0
MEGA = 1000000.0

def measureQoE(bitrates, qualityLevels, stallTimes, startUpDelay, reward=True):
    qualityPlayed = [bitrates[x]/MEGA for x in qualityLevels]
    assert len(qualityPlayed) > 0
    avgQl = qualityPlayed[-1]
    avgQualityVariation = 0 if len(qualityPlayed) == 1 else abs(qualityPlayed[-1] - qualityPlayed[-2])
    if not reward:
        avgQl = sum(qualityPlayed)*1.0/len(qualityPlayed)
        avgQualityVariation = 0 if len(qualityPlayed) == 1 else sum([abs(bt - qualityPlayed[x - 1]) for x,bt in enumerate(qualityPlayed) if x > 0])/(len(qualityPlayed) - 1)

    reward = avgQl \
            - REBUF_PENALTY * stallTimes/10 \
             - SMOOTH_PENALTY * avgQualityVariation

    return reward

def getQoELinear(bitrates, qualityLevels, stallTimes, startUpDelay, reward=True):
    VIDEO_BIT_RATE = bitrates
    # -- linear reward --V
    # reward is video quality - rebuffer penalty - smoothness
    reward = VIDEO_BIT_RATE[bit_rate] / M_IN_K \
             - REBUF_PENALTY * rebuf \
             - SMOOTH_PENALTY * np.abs(VIDEO_BIT_RATE[bit_rate] -
                                       VIDEO_BIT_RATE[last_bit_rate]) / M_IN_K

    # -- log scale reward --
    # log_bit_rate = np.log(VIDEO_BIT_RATE[bit_rate] / float(VIDEO_BIT_RATE[-1]))
    # log_last_bit_rate = np.log(VIDEO_BIT_RATE[last_bit_rate] / float(VIDEO_BIT_RATE[-1]))

    # reward = log_bit_rate \
    #          - REBUF_PENALTY * rebuf \
    #          - SMOOTH_PENALTY * np.abs(log_bit_rate - log_last_bit_rate)

    # -- HD reward --
    # reward = HD_REWARD[bit_rate] \
    #          - REBUF_PENALTY * rebuf \
    #          - SMOOTH_PENALTY * np.abs(HD_REWARD[bit_rate] - HD_REWARD[last_bit_rate])

