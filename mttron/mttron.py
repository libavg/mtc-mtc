#!/usr/bin/env python
# -*- coding: utf-8 -*-

# mttron - Multitouch TRON clone

# Copyright (C) 2010 Thomas Schott, <scotch at cs dot tu-berlin dot de>
#
# mttron is free software: You can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# mttron is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with mttron. If not, see <http://www.gnu.org/licenses/>.

from libavg import avg, AVGApp, Point2D


GRID_SIZE = 4

g_player = avg.Player.get()


class Player(object):
    def __init__(self, parentNode, startPos):
        self.__parentNode = parentNode
        self.__heading = Point2D(0, -GRID_SIZE)
        self.__node = g_player.createNode('circle', {'pos':startPos, 'r':3})
        self.__parentNode.appendChild(self.__node)
        self.__lines = []
        self.__createLine()

    def step(self):
        self.__node.pos += self.__heading
        self.__lines[0].pos2 = self.__node.pos

    def changeHeading(self, heading):
        if self.__heading.x == 0:
            self.__heading.x = heading * self.__heading.y
            self.__heading.y = 0
        else:
            self.__heading.y = -heading * self.__heading.x
            self.__heading.x = 0
        self.__createLine()

    def __createLine(self):
        self.__lines.insert(0, g_player.createNode('line',
                {'pos1':self.__node.pos, 'pos2':self.__node.pos}))
        self.__parentNode.appendChild(self.__lines[0])


class MtTron(AVGApp):
    multitouch = True

    def init(self):
        screenSize = self._parentNode.size
        self.__player = Player(self._parentNode, screenSize / 2)
        g_player.setOnFrameHandler(self.__onFrame)

    def onKey(self, event):
        if event.keystring == "left":
            self.__player.changeHeading(1)
        elif event.keystring == "right":
            self.__player.changeHeading(-1)
        else:
            return False
        return True

    def __onFrame(self):
        self.__player.step()


if __name__ == '__main__':
    MtTron.start(resolution = (1280, 720))

