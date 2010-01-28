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
from random import choice, randint


BORDER_WIDTH = 42
GRID_SIZE = 4

g_player = avg.Player.get()


#def logMsg(msg):
#    print '[%s] %s' %(g_player.getFrameTime(), msg)


class Button(object):
    def __init__(self, parentNode, color, icon, callback):
        w, h = parentNode.size
        if icon == '<':
            self.__node = g_player.createNode('polygon',
                    {'pos':[(0, h / 2), (w / 2 - GRID_SIZE, 0), (w / 2 - GRID_SIZE, h)]})
        elif icon == '>':
            self.__node = g_player.createNode('polygon',
                    {'pos':[(w, h / 2), (w / 2 + GRID_SIZE, 0), (w / 2 + GRID_SIZE, h)]})
        elif icon == 'O':
            self.__node = g_player.createNode('circle',
                        {'pos':parentNode.size / 2, 'r':h / 4, 'strokewidth':2})
        else:
            r = h / 2
            if icon == 'Ol':
                posX = r
            else:
                posX = w - r
            self.__node = g_player.createNode('circle',
                    {'pos':(posX, r), 'r':r})
        self.__node.color = color
        self.__node.opacity = 0
        self.__node.sensitive = False
        parentNode.appendChild(self.__node)

        self.__cursorID = None
        self.__callback = callback
        self.__node.setEventHandler(avg.CURSORDOWN, avg.MOUSE | avg.TOUCH, self.__onDown)
        self.__node.setEventHandler(avg.CURSORUP, avg.MOUSE | avg.TOUCH, self.__onUp)

    def activate(self):
        self.__node.fillopacity = 0.2 # needs libavg-r4503 bugfix to avoid crash
        avg.fadeIn(self.__node, 200, 0.5)
        self.__node.sensitive = True

    def deactivate(self):
        def hideFill():
            self.__node.fillopacity = 0

        if not self.__cursorID is None:
            self.__node.releaseEventCapture(self.__cursorID)
            self.__cursorID = None
        self.__node.sensitive = False
        avg.fadeOut(self.__node, 200, hideFill)

    def __onDown(self, event):
        if not self.__cursorID is None:
            return False
        self.__cursorID = event.cursorid
        self.__node.setEventCapture(self.__cursorID)

        avg.LinearAnim(self.__node, 'fillopacity', 200, 1, 0.2).start() # libavg-r4503
        self.__callback()
        return True # stop event propagation

    def __onUp(self, event):
        if not self.__cursorID == event.cursorid:
            return False
        self.__node.releaseEventCapture(self.__cursorID)
        self.__cursorID = None
        return True # stop event propagation


class Controller(object):
    def __init__(self, parentNode, player, joinCallback, pos, size):
        self.__player = player
        self.__joinCallback = joinCallback

        self.__node = g_player.createNode('div', {'pos':pos, 'size':size, 'crop':False})
#        self.__node.elementoutlinecolor = self.__player.color
        parentNode.appendChild(self.__node)

        if(pos[0] > parentNode.size.x / 2):
            icon = 'Or'
        else:
            icon = 'Ol'
        self.__joinButton = Button(self.__node, self.__player.color, icon,
                self.__joinPlayer)

        if(pos[1] > parentNode.size.y / 2):
            direction = 1
        else:
            direction = -1
        self.__leftButton = Button(self.__node, self.__player.color, '<',
                lambda: self.__player.changeHeading(direction))
        self.__rightButton = Button(self.__node, self.__player.color, '>',
                lambda: self.__player.changeHeading(-direction))

        self.__player.registerController(self)

    def preStart(self):
        self.__joinButton.activate()
        self.__playerJoined = False

    def start(self):
        if self.__playerJoined:
            self.__node.sensitive = True

    def deactivateUnjoined(self):
        if not self.__playerJoined:
            self.__joinButton.deactivate()

    def deactivate(self):
        self.__leftButton.deactivate()
        self.__rightButton.deactivate()

    def __joinPlayer(self):
        self.__joinButton.deactivate()
        self.__node.sensitive = False
        self.__leftButton.activate()
        self.__rightButton.activate()
        self.__joinCallback(self.__player)
        self.__player.setReady()
        self.__playerJoined = True


class Player(object):
    def __init__(self, parentNode, color, startPos, startHeading):
        self.__color = color
        self.__startPos = Point2D(startPos)
        self.__startHeading = Point2D(startHeading)
        self.__lines = []

        self.__div = g_player.createNode('div', {'size':parentNode.size, 'opacity':0})
        parentNode.appendChild(self.__div)
        self.__node = g_player.createNode('div', {'pivot':(0, 0), 'crop':False})
        self.__div.appendChild(self.__node)
        self.__node.appendChild(g_player.createNode('circle',
                {'r':GRID_SIZE, 'color':self.__color,
                 'fillcolor':self.__color, 'fillopacity':1}))
        self.__node.appendChild(g_player.createNode('line',
                {'pos1':(-GRID_SIZE * 2, 0), 'pos2':(GRID_SIZE * 2, 0),
                 'color':self.__color, 'strokewidth':3}))
        self.__node.appendChild(g_player.createNode('line',
                {'pos1':(0, -GRID_SIZE * 2), 'pos2':(0, GRID_SIZE * 2),
                 'color':self.__color, 'strokewidth':3}))
        self.__nodeAnimID = avg.ContinuousAnim(self.__node, 'angle', 0, 3.14)

    @property
    def color(self):
        return self.__color

    @property
    def lines(self):
        return self.__lines

    def registerController(self, controller):
        self.__controller = controller

    def setReady(self):
        self.__node.pos = self.__startPos
        self.__heading = Point2D(self.__startHeading)
        self.__nodeAnimID.start()
        avg.fadeIn(self.__div, 200)
        self.__createLine()

    def setDead(self):
        def removeLines():
            for l in self.__lines:
                l.unlink()
            self.__lines = []

        self.__controller.deactivate()
        self.__nodeAnimID.abort()
        avg.fadeOut(self.__div, 200, removeLines)

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
                or pos.x == self.__div.width or pos.y == self.__div.height:
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
                {'pos1':self.__node.pos, 'pos2':self.__node.pos,
                 'color':self.__color, 'strokewidth':2}))
        self.__div.appendChild(self.__lines[0])


class BgAnim(object):
    def __init__(self, parentNode):
        self.__maxX, self.__maxY = parentNode.size
        self.__heading = Point2D(randint(-1, 1), 0)
        if self.__heading.x == 0:
            self.__heading.y = choice([-1, 1])

        self.__node = g_player.createNode('div',
                {'pos':parentNode.size / 2, 'crop':False, 'opacity':0.2})
        parentNode.appendChild(self.__node)
        self.__node.appendChild(g_player.createNode('line',
                {'pos1':(-self.__maxX, 0), 'pos2':(self.__maxX, 0)}))
        self.__node.appendChild(g_player.createNode('line',
                {'pos1':(0, -self.__maxY), 'pos2':(0, self.__maxY)}))

        self.__headingCountdown = randint(60, 120)
        g_player.setOnFrameHandler(self.__onFrame)

    def __onFrame(self):
        if self.__headingCountdown == 0:
            self.__headingCountdown = randint(60, 120)
            if self.__heading.x == 0:
                self.__heading.x = choice([-1, 1])
                self.__heading.y = 0
            else:
                self.__heading.x = 0
                self.__heading.y = choice([-1, 1])
        else:
            self.__headingCountdown -= 1

        self.__node.pos += self.__heading
        if self.__node.pos.x == 0 or self.__node.pos.x == self.__maxX \
                or self.__node.pos.y == 0 or self.__node.pos.y == self.__maxY:
            self.__heading *= -1
            self.__node.pos += self.__heading


class MtTron(AVGApp):
    multitouch = True

    def init(self):
        screenSize = self._parentNode.size
        battlegroundSize = Point2D(
                floor((screenSize.x - BORDER_WIDTH * 2) / GRID_SIZE) * GRID_SIZE,
                floor((screenSize.y - BORDER_WIDTH * 2) / GRID_SIZE) * GRID_SIZE)

        self._parentNode.appendChild(g_player.createNode('rect',
                {'size':screenSize,
                 'opacity':0, 'fillcolor':'B00000', 'fillopacity':1}))
        self._parentNode.appendChild(g_player.createNode('rect',
                {'pos':(BORDER_WIDTH, BORDER_WIDTH), 'size':battlegroundSize,
                 'opacity':0, 'fillcolor':'000000', 'fillopacity':1}))

        gameDiv = g_player.createNode('div',
                {'pos':(BORDER_WIDTH, BORDER_WIDTH), 'size':battlegroundSize})
        self._parentNode.appendChild(gameDiv)
        ctrlDiv = g_player.createNode('div',
                {'pos':gameDiv.pos, 'size':gameDiv.size})
        self._parentNode.appendChild(ctrlDiv)

        BgAnim(gameDiv)
        BgAnim(gameDiv)
        BgAnim(gameDiv)
        BgAnim(gameDiv)

        ctrlSize = Point2D(GRID_SIZE * 64, GRID_SIZE * 32)
        self.__controllers = []
        # 1st
        p = Player(gameDiv, '00FF00',
                ctrlSize, (GRID_SIZE, 0))
        self.__controllers.append(Controller(ctrlDiv, p, self.joinPlayer,
                (4, 4), ctrlSize))
        # 2nd
        p = Player(gameDiv, 'FF00FF',
                (ctrlDiv.size.x - ctrlSize.x, ctrlSize.y), (-GRID_SIZE, 0))
        self.__controllers.append(Controller(ctrlDiv, p, self.joinPlayer,
                (ctrlDiv.size.x - ctrlSize.x - 4, 4), ctrlSize))
        # 3rd
        p = Player(gameDiv, '00FFFF',
                (ctrlSize.x, ctrlDiv.size.y - ctrlSize.y), (GRID_SIZE, 0))
        self.__controllers.append(Controller(ctrlDiv, p, self.joinPlayer,
                (4, ctrlDiv.size.y - ctrlSize.y - 4), ctrlSize))
        # 4th
        p = Player(gameDiv, 'FFFF00',
                (ctrlDiv.size.x - ctrlSize.x, ctrlDiv.size.y - ctrlSize.y),
                (-GRID_SIZE, 0))
        self.__controllers.append(Controller(ctrlDiv, p, self.joinPlayer,
                (ctrlDiv.size.x - ctrlSize.x - 4, ctrlDiv.size.y - ctrlSize.y - 4),
                ctrlSize))

        self.__startButton = Button(ctrlDiv, 'FF0000', 'O', self.__start)
        self.__countdownNode = g_player.createNode('circle',
                {'pos':ctrlDiv.size / 2, 'r':ctrlDiv.size.y / 4,
                 'opacity':0, 'sensitive':False})
        ctrlDiv.appendChild(self.__countdownNode)

        self.__preStart()

    def joinPlayer(self, player):
        self.__activePlayers.append(player)
        if len(self.__activePlayers) == 2:
            self.__startButton.activate()

    def __preStart(self):
        self.__activePlayers = []
        for c in self.__controllers:
            c.preStart()

    def __start(self):
        def goGreen():
            self.__countdownNode.fillcolor = '00FF00'
            avg.LinearAnim(self.__countdownNode, 'fillopacity', 1000, 1, 0).start()
            for c in self.__controllers:
                c.start()
            self.__onFrameHandlerID = g_player.setOnFrameHandler(self.__onFrame)
        def goYellow():
            self.__countdownNode.fillcolor = 'FFFF00'
            avg.LinearAnim(self.__countdownNode, 'fillopacity', 1000, 1, 0, False,
                    None, goGreen).start()
        def goRed():
            self.__countdownNode.fillcolor = 'FF0000'
            avg.LinearAnim(self.__countdownNode, 'fillopacity', 1000, 1, 0, False,
                    None, goYellow).start()

        self.__startButton.deactivate()
        for c in self.__controllers:
            c.deactivateUnjoined()
        goRed()

    def __stop(self):
        def restart():
            for p in self.__activePlayers:
                p.setDead()
            self.__preStart()
        g_player.clearInterval(self.__onFrameHandlerID)
        g_player.setTimeout(2000, restart)

    def __onFrame(self):
        for p in self.__activePlayers:
            p.step()
        crashedPlayers = []
        for p in self.__activePlayers:
            if p.checkCrash(self.__activePlayers):
                crashedPlayers.append(p)
        if len(self.__activePlayers) == len(crashedPlayers):
            self.__stop()
        else:
            for p in crashedPlayers:
                p.setDead()
                self.__activePlayers.remove(p)
                if len(self.__activePlayers) == 1:
                    self.__stop()


if __name__ == '__main__':
    MtTron.start(resolution = (1280, 720))

