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
    def __init__(self, parentNode, color, startPos, startHeading):
        self.__parentNode = parentNode
        self.__color = color
        self.__startPos = Point2D(startPos)
        self.__startHeading = Point2D(startHeading)
        self.__node = g_player.createNode('circle', {'r':3, 'color':self.__color})
        self.__lines = []

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
        # lines always run rightwards or downwards (for easier collision checking)
        if self.__heading.x < 0 or self.__heading.y < 0:
            self.__lines[0].pos1 = self.__node.pos
        else:
            self.__lines[0].pos2 = self.__node.pos

    def changeHeading(self, heading):
        if self.__heading.x == 0:
            self.__heading.x = heading * self.__heading.y
            self.__heading.y = 0
        else:
            self.__heading.y = -heading * self.__heading.x
            self.__heading.x = 0
        self.__createLine()

    def checkCrash(self, players):
        pos = self.__node.pos
        # check border
        if pos.x == 0 or pos.y == 0 \
                or pos.x == self.__parentNode.width or pos.y == self.__parentNode.height:
            return True
        # check lines
        for p in players:
            if p is self:
                firstLine = 1 # don't check own current line
            else:
                firstLine = 0
            for l in p.lines[firstLine:]:
                if pos.x == l.pos1.x:
                    if l.pos1.y <= pos.y and pos.y <= l.pos2.y:
                        return True
                elif pos.y == l.pos1.y \
                        and l.pos1.x <= pos.x and pos.x <= l.pos2.x:
                    return True
        return False

    def __createLine(self):
        self.__lines.insert(0, g_player.createNode('line',
                {'pos1':self.__node.pos, 'pos2':self.__node.pos, 'color':self.__color}))
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

        self.__players = []
        self.__players.append(Player(self.__gameDiv, '00FF00',
                (GRID_SIZE, GRID_SIZE),
                (GRID_SIZE, 0)))
        self.__players.append(Player(self.__gameDiv, 'FF00FF',
                (battlegroundSize.x - GRID_SIZE, GRID_SIZE),
                (-GRID_SIZE, 0)))
        self.__players.append(Player(self.__gameDiv, '00FFFF',
                (GRID_SIZE, battlegroundSize.y - GRID_SIZE),
                (GRID_SIZE, 0)))
        self.__players.append(Player(self.__gameDiv, 'FFFF00',
                (battlegroundSize.x - GRID_SIZE, battlegroundSize.y - GRID_SIZE),
                (-GRID_SIZE, 0)))

        self.__activePlayers = []
        for p in self.__players:
            self.__activePlayers.append(p)
            p.setReady()

        self.__onFrameHandlerID = g_player.setOnFrameHandler(self.__onFrame)

    def onKey(self, event):
        if event.keystring == "left":
            self.__players[0].changeHeading(1)
        elif event.keystring == "right":
            self.__players[0].changeHeading(-1)
        else:
            return False
        return True

    def __onFrame(self):
        for p in self.__activePlayers:
            p.step()
        crashedPlayers = []
        for p in self.__activePlayers:
            if p.checkCrash(self.__activePlayers):
                crashedPlayers.append(p)
        for p in crashedPlayers:
            p.setDead()
            self.__activePlayers.remove(p)


if __name__ == '__main__':
    MtTron.start(resolution = (1280, 720))

