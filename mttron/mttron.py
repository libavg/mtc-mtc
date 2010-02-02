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
from math import floor, pi
from random import choice, randint


BORDER_WIDTH = 42
GRID_SIZE = 4

g_player = avg.Player.get()
g_exitButtons = True


#def logMsg(msg):
#    print '[%s] %s' %(g_player.getFrameTime(), msg)


class Button(object):
    def __init__(self, parentNode, color, icon, callback):
        w, h = parentNode.size
        if icon == '^':
            self.__node = g_player.createNode('polygon',
                    {'pos':[(w, h), (0, h), (0, 0)]})
        elif icon == '<':
            self.__node = g_player.createNode('polygon',
                    {'pos':[(GRID_SIZE, 0), (w, 0), (w, h - GRID_SIZE)]})
        elif icon == '>':
            self.__node = g_player.createNode('polygon',
                    {'pos':[(w - GRID_SIZE, h), (0, h), (0, GRID_SIZE)]})
        elif icon == '#':
            # WinCounter size + some offset
            size = Point2D(GRID_SIZE * 44, GRID_SIZE * 44)
            self.__node = g_player.createNode('rect',
                    {'pos':parentNode.size / 2 - size, 'size':size * 2})
        elif icon == 'xr':
            size = Point2D(GRID_SIZE * 22, GRID_SIZE * 22)
            self.__node = g_player.createNode('rect',
                {'pos': parentNode.size / 2 - size + Point2D(GRID_SIZE * 88, 0),
                'size':size * 2, 'angle': pi / 4.0})
        elif icon == 'xl':
            size = Point2D(GRID_SIZE * 22, GRID_SIZE * 22)
            self.__node = g_player.createNode('rect',
                    {'pos': parentNode.size / 2 - size - Point2D(GRID_SIZE * 88, 0),
                    'size':size * 2, 'angle': pi / 4.0})
        else:
            if icon == 'O':
                self.__node = g_player.createNode('circle',
                            {'pos':parentNode.size / 2, 'r':h / 4, 'strokewidth':2})
            else:
                self.__node = g_player.createNode('circle',
                            {'pos':parentNode.size / 2, 'r':h / 2})
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
    def __init__(self, parentNode, player, joinCallback, pos, size, angle):
        self.__player = player
        self.__joinCallback = joinCallback

        self.__node = g_player.createNode('div',
                {'pos':pos, 'size':(size, size),
                 'angle':angle, 'pivot':(0, 0), 'crop':False})
        parentNode.appendChild(self.__node)

        self.__joinButton = Button(self.__node, self.__player.color, 'o',
                self.__joinPlayer)
        self.__leftButton = Button(self.__node, self.__player.color, '<',
                lambda: self.__player.changeHeading(1))
        self.__rightButton = Button(self.__node, self.__player.color, '>',
                lambda: self.__player.changeHeading(-1))

        self.__player.registerController(self)

    def preStart(self, clearWins):
        self.__joinButton.activate()
        self.__node.sensitive = True
        self.__playerJoined = False
        if clearWins:
            self.__player.clearWins()

    def start(self):
        if self.__playerJoined:
            self.__node.sensitive = True

    def deactivateUnjoined(self):
        if not self.__playerJoined:
            self.__joinButton.deactivate()
            self.__node.sensitive = False

    def deactivate(self):
        self.__leftButton.deactivate()
        self.__rightButton.deactivate()
        self.__node.sensitive = False

    def __joinPlayer(self):
        self.__joinButton.deactivate()
        self.__node.sensitive = False
        self.__leftButton.activate()
        self.__rightButton.activate()
        self.__joinCallback(self.__player)
        self.__player.setReady()
        self.__playerJoined = True


class WinCounter(object):
    def __init__(self, parentNode, size, angle, color):
        def triangle(p0, p1, p2):
            t = g_player.createNode('polygon',
                    {'pos':[p0, p1, p2], 'color':color, 'fillcolor':color})
            self.__node.appendChild(t)

        self.__count = 0
        self.__node = g_player.createNode('div',
                {'pos':parentNode.size / 2 + Point2D(GRID_SIZE, GRID_SIZE),
                 'size':(size, size),
                 'angle':angle, 'pivot':(-GRID_SIZE, -GRID_SIZE), 'crop':False})
        parentNode.appendChild(self.__node)

        s12 = size / 2
        s14 = size / 4
        s34 = size * 3 / 4
        triangle((0, 0), (s14, s14), (0, s12))
        triangle((0, s12), (s14, s14), (s12, s12))
        triangle((s12, s12), (s14, s34), (0, s12))
        triangle((0, s12), (s14, s34), (0, size))
        triangle((0, size), (s14, s34), (s12, size))
        triangle((s12, size), (s14, s34), (s12, s12))
        triangle((s12, s12), (s34, s34), (s12, size))
        triangle((s12, size), (s34, s34), (size, size))

        resetButton = Button(self.__node, color, '^', self.reset)
        resetButton.activate()

    @property
    def count(self):
        return self.__count

    def inc(self):
        self.__node.getChild(self.__count).fillopacity = 0.5
        self.__count += 1

    def reset(self):
        for i in range(0, self.__count):
            self.__node.getChild(i).fillopacity = 0
        self.__count = 0


class Player(object):
    def __init__(self, parentNode, color, startPos, startHeading,
            winsDiv, winsSize, winsAngle):
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
        self.__nodeAnim = avg.ContinuousAnim(self.__node, 'angle', 0, 3.14)

        self.__wins = WinCounter(winsDiv, winsSize, winsAngle, self.__color)
        self.incWins = self.__wins.inc
        self.clearWins = self.__wins.reset

    @property
    def color(self):
        return self.__color

    @property
    def lines(self):
        return self.__lines

    @property
    def wins(self):
        return self.__wins.count

    def registerController(self, controller):
        self.__controller = controller

    def setReady(self):
        self.__node.pos = self.__startPos
        self.__heading = Point2D(self.__startHeading)
        self.__shield = None
        self.__nodeAnim.start()
        avg.fadeIn(self.__div, 200)
        self.__createLine()

    def setDead(self):
        def removeLines():
            for l in self.__lines:
                l.unlink()
            self.__lines = []

        if not self.__shield is None:
            self.__shield.jump()
        self.__controller.deactivate()
        self.__nodeAnim.abort()
        avg.fadeOut(self.__div, 200, removeLines)

    def step(self):
        self.__node.pos += self.__heading
        if not self.__shield is None:
            self.__shield.move(self.__node.pos)
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

    def checkCrash(self, players, blocker):
        pos = self.__node.pos
        # check border
        if pos.x == 0 or pos.y == 0 \
                or pos.x == self.__div.width or pos.y == self.__div.height:
            return True
        # check blocker
        if blocker.checkCollision(pos):
            return True
        # check lines
        for p in players:
            if p is self:
                firstLine = 1 # don't check own current line
            else:
                firstLine = 0
            for l in p.lines[firstLine:]:
                if pos.x == l.pos1.x \
                        and l.pos1.y <= pos.y and pos.y <= l.pos2.y \
                        or pos.y == l.pos1.y \
                        and l.pos1.x <= pos.x and pos.x <= l.pos2.x:
                    if self.__shield is None:
                        return True
                    self.__shield.jump()
                    self.__shield = None
        return False

    def checkShield(self, shield):
        if shield.checkCollision(self.__node.pos):
            self.__shield = shield
            self.__shield.grab()

    def __createLine(self):
        self.__lines.insert(0, g_player.createNode('line',
                {'pos1':self.__node.pos, 'pos2':self.__node.pos,
                 'color':self.__color, 'strokewidth':2}))
        self.__div.appendChild(self.__lines[0])


class DragItem(object):
    def __init__(self, parentNode, iconNode):
        self._posOffset = Point2D(GRID_SIZE * 4, GRID_SIZE * 4)
        self.__minPosX = int(-self._posOffset.x) + GRID_SIZE
        self.__maxPosX = int(parentNode.size.x - self._posOffset.x)
        self.__posX = range(self.__minPosX, self.__maxPosX, GRID_SIZE)
        self.__minPosY = int(-self._posOffset.y) + GRID_SIZE
        self.__maxPosY = int(parentNode.size.y - self._posOffset.y)
        self.__posY = range(self.__minPosY, self.__maxPosY, GRID_SIZE)

        self._div = g_player.createNode('div', {'size':self._posOffset * 2})
        parentNode.appendChild(self._div)
        self.__node = iconNode
        self.__node.opacity = 0
        self._div.appendChild(self.__node)

        self.__cursorID = None
        self._div.setEventHandler(avg.CURSORDOWN, avg.MOUSE | avg.TOUCH, self._onDown)
        self._div.setEventHandler(avg.CURSORUP, avg.MOUSE | avg.TOUCH, self.__onUp)
        self._div.setEventHandler(avg.CURSORMOTION, avg.MOUSE | avg.TOUCH, self.__onMotion)

    def activate(self):
        self.__active = True
        self.__flash()

    def deactivate(self):
        self.__active = False

    def jump(self):
        self._div.pos = (choice(self.__posX), choice(self.__posY))

    def checkCollision(self, pos):
        if not self.__cursorID is None:
            return False # no collision when dragging
        dist = self._div.pos + self._posOffset - pos
        if abs(dist.x) <= GRID_SIZE and abs(dist.y) <= GRID_SIZE:
            return True
        return False

    def __flash(self):
        if self.__active:
            avg.LinearAnim(self.__node, 'opacity', 600, 1, 0, False,
                    None, self.__flash).start()

    def _onDown(self, event):
        if not self.__cursorID is None:
            return False
        self.__cursorID = event.cursorid
        self._div.setEventCapture(self.__cursorID)
        self.__dragOffset = event.pos - self._div.pos
        return True

    def __onUp(self, event):
        if not self.__cursorID == event.cursorid:
            return False
        self._div.releaseEventCapture(self.__cursorID)
        self.__cursorID = None
        return True

    def __onMotion(self, event):
        if not self.__cursorID == event.cursorid:
            return False
        pos = (event.pos - self.__dragOffset) / GRID_SIZE
        pos = Point2D(round(pos.x), round(pos.y)) * GRID_SIZE
        if self.__minPosX <= pos.x and pos.x < self.__maxPosX \
                and self.__minPosY <= pos.y and pos.y < self.__maxPosY:
            self._div.pos = pos
        return True


class Shield(DragItem):
    def __init__(self, parentNode):
        icon = g_player.createNode('circle', {'r':GRID_SIZE * 2})
        super(Shield, self).__init__(parentNode, icon)
        icon.pos = self._posOffset

    def jump(self):
        super(Shield, self).jump()
        self.__isGrabbed = False

    def move(self, pos):
        self._div.pos = pos - self._posOffset

    def checkCollision(self, pos):
        if self.__isGrabbed:
            return False
        return super(Shield, self).checkCollision(pos)

    def grab(self):
        self.__isGrabbed = True

    def _onDown(self, event):
        if self.__isGrabbed:
            return False
        return super(Shield, self)._onDown(event)


class Blocker(DragItem):
    def __init__(self, parentNode):
        icon = g_player.createNode('rect',
                {'size':(GRID_SIZE * 3, GRID_SIZE * 3), 'color':'FF0000'})
        super(Blocker, self).__init__(parentNode, icon)
        icon.pos = self._posOffset - icon.size / 2


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
        self.__onFrameHandlerID = None

    def start(self):
        self.__onFrameHandlerID = g_player.setOnFrameHandler(self.__onFrame)

    def stop(self):
        assert self.__onFrameHandlerID is not None
        g_player.clearInterval(self.__onFrameHandlerID)

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

        ctrlSize = GRID_SIZE * 42
        gameDiv = g_player.createNode('div',
                {'pos':(BORDER_WIDTH, BORDER_WIDTH), 'size':battlegroundSize})
        self._parentNode.appendChild(gameDiv)
        ctrlDiv = g_player.createNode('div',
                {'pos':gameDiv.pos, 'size':gameDiv.size})
        self._parentNode.appendChild(ctrlDiv)
        self.__winsDiv = g_player.createNode('div',
                {'size':gameDiv.size, 'opacity':0, 'crop':False, 'sensitive':False})
        ctrlDiv.appendChild(self.__winsDiv)

        self.__bgAnims = []
        for i in xrange(0, 4):
            self.__bgAnims.append(BgAnim(gameDiv))

        self.__shield = Shield(ctrlDiv)
        self.__blocker = Blocker(ctrlDiv)

        playerPos = ctrlSize + GRID_SIZE * 2
        self.__controllers = []
        # 1st
        p = Player(gameDiv, '00FF00',
                (playerPos, playerPos), (GRID_SIZE, 0),
                self.__winsDiv, ctrlSize, pi)
        self.__controllers.append(Controller(ctrlDiv, p, self.joinPlayer,
                (GRID_SIZE, GRID_SIZE), ctrlSize, 0))
        # 2nd
        p = Player(gameDiv, 'FF00FF',
                (ctrlDiv.size.x - playerPos, playerPos), (-GRID_SIZE, 0),
                self.__winsDiv, ctrlSize, -pi / 2)
        self.__controllers.append(Controller(ctrlDiv, p, self.joinPlayer,
                (ctrlDiv.size.x - GRID_SIZE, GRID_SIZE), ctrlSize, pi / 2))
        # 3rd
        p = Player(gameDiv, '00FFFF',
                (playerPos, ctrlDiv.size.y - playerPos), (GRID_SIZE, 0),
                self.__winsDiv, ctrlSize, pi / 2)
        self.__controllers.append(Controller(ctrlDiv, p, self.joinPlayer,
                (GRID_SIZE, ctrlDiv.size.y - GRID_SIZE), ctrlSize, -pi / 2))
        # 4th
        p = Player(gameDiv, 'FFFF00',
                (ctrlDiv.size.x - playerPos, ctrlDiv.size.y - playerPos),
                (-GRID_SIZE, 0),
                self.__winsDiv, ctrlSize, 0)
        self.__controllers.append(Controller(ctrlDiv, p, self.joinPlayer,
                (ctrlDiv.size.x - GRID_SIZE, ctrlDiv.size.y - GRID_SIZE),
                ctrlSize, pi))

        self.__startButton = Button(ctrlDiv, 'FF0000', 'O', self.__start)
        self.__clearButton = Button(ctrlDiv, 'FF0000', '#', self.__clearWins)
        self.__countdownNode = g_player.createNode('circle',
                {'pos':ctrlDiv.size / 2, 'r':ctrlDiv.size.y / 4,
                 'opacity':0, 'sensitive':False})
        ctrlDiv.appendChild(self.__countdownNode)

        if g_exitButtons:
            Button(self.__winsDiv, 'FF0000', 'xl', self.leave).activate()
            Button(self.__winsDiv, 'FF0000', 'xr', self.leave).activate()

        self.__preStart()

    def joinPlayer(self, player):
        self.__activePlayers.append(player)
        if len(self.__activePlayers) == 1:
            avg.fadeOut(self.__winsDiv, 200)
            self.__winsDiv.sensitive = False
        elif len(self.__activePlayers) == 2:
            self.__startButton.activate()

    def _enter(self):
        for bga in self.__bgAnims:
            bga.start()

    def _leave(self):
        for bga in self.__bgAnims:
            bga.stop()

    def __preStart(self, clearWins=False):
        self.__activePlayers = []
        for c in self.__controllers:
            c.preStart(clearWins)
        self.__shield.jump()
        self.__blocker.jump()

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
            self.__shield.activate()
            self.__blocker.activate()
        def goRed():
            self.__countdownNode.fillcolor = 'FF0000'
            avg.LinearAnim(self.__countdownNode, 'fillopacity', 1000, 1, 0, False,
                    None, goYellow).start()

        self.__startButton.deactivate()
        for c in self.__controllers:
            c.deactivateUnjoined()
        goRed()

    def __stop(self, forceClearWins=False):
        def restart():
            for p in self.__activePlayers:
                p.setDead()
            avg.fadeIn(self.__winsDiv, 200)
            self.__winsDiv.sensitive = True
            if forceClearWins:
                self.__clearButton.activate()
            else:
                self.__preStart()

        g_player.clearInterval(self.__onFrameHandlerID)
        self.__shield.deactivate()
        self.__blocker.deactivate()
        g_player.setTimeout(2000, restart)

    def __clearWins(self):
        self.__clearButton.deactivate()
        self.__preStart(True)

    def __onFrame(self):
        for p in self.__activePlayers:
            p.step()

        crashedPlayers = []
        for p in self.__activePlayers:
            if p.checkCrash(self.__activePlayers, self.__blocker):
                crashedPlayers.append(p)
        for p in crashedPlayers:
            p.setDead()
            self.__activePlayers.remove(p)

        if len(self.__activePlayers) == 0:
            self.__stop()
        elif len(self.__activePlayers) == 1:
            self.__activePlayers[0].incWins()
            if self.__activePlayers[0].wins == 8:
                self.__stop(True)
            else:
                self.__stop()
        else:
            for p in self.__activePlayers:
                p.checkShield(self.__shield)


if __name__ == '__main__':
    g_exitButtons = False
    MtTron.start(resolution = (1280, 720))

