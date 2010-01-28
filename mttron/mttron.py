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
from math import floor


BORDER_WIDTH = 42
GRID_SIZE = 4

g_player = avg.Player.get()


#def logMsg(msg):
#    print '[%s] %s' %(g_player.getFrameTime(), msg)


class Player(object):
    def __init__(self, parentNode, startPos, startHeading):
        self.__parentNode = parentNode
        self.__startPos = startPos
        self.__startHeading = startHeading
        self.__node = g_player.createNode('circle', {'r':3})
        self.__lines = []

    @property
    def pos(self):
        return self.__node.pos

    @property
    def lines(self):
        return self.__lines

    def setReady(self):
        self.__node.pos = self.__startPos
        self.__parentNode.appendChild(self.__node)
        self.__heading = Point2D(self.__startHeading)
        self.__createLine()

    def setDead(self):
        self.__node.unlink()
        for l in self.__lines:
            l.unlink()
        self.__lines = []

    def step(self):
        self.__node.pos += self.__heading
        self.__lines[0].pos2 = self.__node.pos

    def changeHeading(self, heading):
        if len(self.__lines):
            if self.__heading.x < 0 or self.__heading.y < 0:
                pos1 = self.__lines[0].pos1
                self.__lines[0].pos1 = self.__lines[0].pos2
                self.__lines[0].pos2 = pos1
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
        battlegroundSize = Point2D(
                floor((screenSize.x - BORDER_WIDTH * 2) / GRID_SIZE) * GRID_SIZE,
                floor((screenSize.y - BORDER_WIDTH * 2) / GRID_SIZE) * GRID_SIZE)

        self.__gameDiv = g_player.createNode('div',
                {'pos':(BORDER_WIDTH, BORDER_WIDTH), 'size':battlegroundSize})
        self.__gameDiv.elementoutlinecolor = 'FF0000'
        self._parentNode.appendChild(self.__gameDiv)

        self.__player = Player(self.__gameDiv,
                Point2D(battlegroundSize.x / 2 + 2, battlegroundSize.y / 2 + 2),
                Point2D(0, -GRID_SIZE))
        self.__player.setReady()

        self.__onFrameHandlerID = g_player.setOnFrameHandler(self.__onFrame)

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
        playerPos = self.__player.pos
        if playerPos.x == 0 \
                or playerPos.y == 0 \
                or playerPos.x == self.__gameDiv.width \
                or playerPos.y == self.__gameDiv.height:
            self.__player.setDead()
            self.__player.setReady()
        for l in self.__player.lines[1:]:
            if playerPos.x == l.pos1.x:
                if l.pos1.y <= playerPos.y and playerPos.y <= l.pos2.y:
                    self.__player.setDead()
                    self.__player.setReady()
            elif playerPos.y == l.pos1.y:
                if l.pos1.x <= playerPos.x and playerPos.x <= l.pos2.x:
                    self.__player.setDead()
                    self.__player.setReady()


if __name__ == '__main__':
    MtTron.start(resolution = (1280, 720))

