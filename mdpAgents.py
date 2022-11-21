# mdpAgents.py
# parsons/20-nov-2017
#
# Version 1
#
# The starting point for CW2.
#
# Intended to work with the PacMan AI projects from:
#
# http://ai.berkeley.edu/
#
# These use a simple API that allow us to control Pacman's interaction with
# the environment adding a layer on top of the AI Berkeley code.
#
# As required by the licensing agreement for the PacMan AI we have:
#
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
#
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).

# The agent here is was written by Simon Parsons, based on the code in
# pacmanAgents.py

from pacman import Directions
from game import Agent
import api
import random
import game
import util


class MDPAgent(Agent):

    # Constructor: this gets run when we first invoke pacman.py
    def __init__(self):
        print "Starting up MDPAgent!"
        name = "Pacman"
        self.valueIterationStart = 0
        self.valueIterationDictionary = {}
        self.lastAction = Directions.STOP
        self.visitedPos = []

    # Gets run after an MDPAgent object is created and once there is
    # game state to access.
    def registerInitialState(self, state):
        print "Running registerInitialState for MDPAgent!"
        print "I'm at:"
        print api.whereAmI(state)
        self.gameMap(state)
        self.visitedPos = []

    # This is what gets run in between multiple games
    def final(self, state):
        print "Looks like the game just ended!"
        self.valueIterationStart = 0
        self.valueIterationDictionary = {}
        self.visitedPos = []

    def addLastPosition(self, lastAction, pacmanPos):
        if lastAction == Directions.STOP: self.visitedPos.append(pacmanPos)
        if lastAction == Directions.NORTH: self.visitedPos.append(pacmanPos[1] + 1)
        if lastAction == Directions.SOUTH: self.visitedPos.append(pacmanPos[1] - 1)
        if lastAction == Directions.EAST: self.visitedPos.append(pacmanPos[0] + 1)
        if lastAction == Directions.WEST: self.visitedPos.append(pacmanPos[0] - 1)


    def gameMap(self, state):
        # Map of all static objects, namely food, capsules and walls.
        stageMap = []

        # Values Map used to assign values to all the different positions/states on the map.
        self.valuesMap = {}

        foodPos = api.food(state)
        capsulePos = api.capsules(state)

        wallPos = api.walls(state)
        mapCornerPos = api.corners(state)

        biggestX = 0
        biggestY = 0
        for i in range(len(mapCornerPos)):
            if mapCornerPos[i][0] > biggestX: biggestX = mapCornerPos[i][0]
            if mapCornerPos[i][1] > biggestY: biggestY = mapCornerPos[i][1]

        mapWidth = biggestX + 1
        mapHeight = biggestY + 1

        for i in range(mapWidth):
            for j in range(mapHeight):
                stageMap.append((i, j))

        # Map of all positions that Pac Man is allowed to go to.
        self.allowedPos = (tuple(set(stageMap) - set(wallPos)))

        ''' --- Initial Values assignment stage --- '''
        for i in range(len(self.allowedPos)):
            # Assign a value of 1 to positions/states with food.
            if self.allowedPos[i] in foodPos: self.valuesMap[self.allowedPos[i]] = 1

            # Assign a value of 2 to positions/states with capsules. Capsules are more value
            # since they give more score points and also allow Pac Man to eat ghosts.
            if self.allowedPos[i] in capsulePos: self.valuesMap[self.allowedPos[i]] = 2

    def updateStaticObjValues(self, state):
        foodPos = api.food(state)
        capsulePos = api.capsules(state)

        # Clear all previous values and make them equal to 0
        for i in range(len(self.allowedPos)): self.valuesMap[self.allowedPos[i]] = 0

        # Assign the new values
        for i in range(len(self.allowedPos)):
            if self.allowedPos[i] in foodPos: self.valuesMap[self.allowedPos[i]] = 1
            if self.allowedPos[i] in capsulePos: self.valuesMap[self.allowedPos[i]] = 2

    def valueIteration(self, state, ghostPos):
        foodPos = api.food(state)
        capsulePos = api.capsules(state)
        wallPos = api.walls(state)

        reward = 0 - 0.04  # value taken from lecture slides
        gamma = 0.8  # value taken from lecture slides

        if self.valueIterationStart == 0:
            self.valueIterationDictionary = self.valuesMap.copy()
            self.valueIterationStart = 1
        temp = self.valueIterationDictionary.copy()

        # Assign rewards on the basis of objects on the map such as food, ghost and capsules
        # and calculates utlity of the coordinates using bellman equation
        for i in range(len(self.allowedPos)):

            if self.allowedPos[i] in foodPos: reward = 1
            if self.allowedPos[i] in capsulePos: reward = 2
            if self.allowedPos[i] in ghostPos: reward = -80
            if self.allowedPos[i] not in foodPos and self.allowedPos[i] not in capsulePos: reward = -5
            if self.allowedPos[i] in self.visitedPos: reward = -10

            northNeighbour = southNeighbour = eastNeighbour = westNeighbour = eastNeighbour = self.allowedPos[i]

            # North Coordinates
            if (self.allowedPos[i][0], self.allowedPos[i][1] + 1) not in wallPos:
                northNeighbour = (self.allowedPos[i][0], self.allowedPos[i][1] + 1)
            # South Coordinates
            if (self.allowedPos[i][0], self.allowedPos[i][1] - 1) not in wallPos:
                southNeighbour = (self.allowedPos[i][0], self.allowedPos[i][1] - 1)
            # East Coordinates
            if (self.allowedPos[i][0] + 1, self.allowedPos[i][1]) not in wallPos:
                eastNeighbour = (self.allowedPos[i][0] + 1, self.allowedPos[i][1])
            # West Coordinates
            if (self.allowedPos[i][0] - 1, self.allowedPos[i][1]) not in wallPos:
                westNeighbour = (self.allowedPos[i][0] - 1, self.allowedPos[i][1])



            # Bellman Equation. Calculating utility from the last iterated values
            northNeighbourValue = (
                    (0.8 * temp[northNeighbour]) + (0.1 * temp[westNeighbour]) + (0.1 * temp[eastNeighbour]))
            eastNeighbourValue = (
                    (0.8 * temp[eastNeighbour]) + (0.1 * temp[northNeighbour]) + (0.1 * temp[southNeighbour]))
            southNeighbourValue = (
                    (0.8 * temp[southNeighbour]) + (0.1 * temp[westNeighbour]) + (0.1 * temp[eastNeighbour]))
            westNeighbourValue = (
                    (0.8 * temp[westNeighbour]) + (0.1 * temp[northNeighbour]) + (0.1 * temp[southNeighbour]))

            valueIteration = reward + (
                    gamma * max(northNeighbourValue, eastNeighbourValue, southNeighbourValue, westNeighbourValue))

            # The iteration value is rounded off to 3 decimals
            self.valueIterationDictionary[self.allowedPos[i]] = round(valueIteration, 3)

        # This compares all the current value iteration dictionary and the previous one
        stability = cmp(temp, self.valueIterationDictionary)
        return stability

    def findGhostsRange(self, state):
        ghoststates = api.ghostStates(state)
        ghostsRange = []
        # Making a list of ghost coordinates which are still active and not edible
        # So these ghost coordinates will get negative value during iteration
        for i in range(len(ghoststates)):
            # converting ghosts coordinates in integer
            ghostX = ghoststates[i][0][0]
            ghostY = ghoststates[i][0][1]

            # Current ghost position
            ghostPos = (int(ghostX), int(ghostY))

            if ghostPos in self.allowedPos and ghoststates[i][1] == 0:
                # Add Current Ghost Position to the Ghost Range
                ghostsRange.append(ghostPos)

                # Add the position North of the Ghost to the Ghost Range
                ghostsRange.append((ghostPos[0], ghostPos[1] + 1))
                # Add the position South of the Ghost to the Ghost Range
                ghostsRange.append((ghostPos[0], ghostPos[1] - 1))
                # Add the position East of the Ghost to the Ghost Range
                ghostsRange.append((ghostPos[0] + 1, ghostPos[1]))
                # Add the position West of the Ghost to the Ghost Range
                ghostsRange.append((ghostPos[0] - 1, ghostPos[1]))

                # Add the position North-West of the Ghost to the Ghost Range
                ghostsRange.append((ghostPos[0] - 1, ghostPos[1] + 1))
                # Add the position North-East of the Ghost to the Ghost Range
                ghostsRange.append((ghostPos[0] + 1, ghostPos[1] + 1))
                # Add the position South-West of the Ghost to the Ghost Range
                ghostsRange.append((ghostPos[0] - 1, ghostPos[1] - 1))
                # Add the position South-East of the Ghost to the Ghost Range
                ghostsRange.append((ghostPos[0] + 1, ghostPos[1] - 1))


        ghostsRange = list(dict.fromkeys(ghostsRange))

        return ghostsRange

    # For now I just move randomly
    def getAction(self, state):
        # Get the actions we can try, and remove "STOP" if that is one of them.
        legal = api.legalActions(state)
        if Directions.STOP in legal: legal.remove(Directions.STOP)

        pacmanPos = api.whereAmI(state)

        self.updateStaticObjValues(state)

        ghostsRange = self.findGhostsRange(state)

        # The value iteration will be called until all the value of the bellman
        # stops changing from the previous values
        while True:
            try:
                stable = self.valueIteration(state, ghostsRange)
                if stable == 0: break
            except:
                pass
                break

        # If the move is illegal, we keep the neighbor's position equal to Pac Mans current position
        # so that Pac Man won't try to go there
        eastNeighbour = westNeighbour = northNeighbour = southNeighbour = pacmanPos

        # North Position
        if Directions.NORTH in legal: northNeighbour = (pacmanPos[0], pacmanPos[1] + 1)
        # South Position
        if Directions.SOUTH in legal: southNeighbour = ((pacmanPos[0], pacmanPos[1] - 1))
        # East Position
        if Directions.EAST in legal: eastNeighbour = (pacmanPos[0] + 1, pacmanPos[1])
        # West Position
        if Directions.WEST in legal: westNeighbour = (pacmanPos[0] - 1, pacmanPos[1])


        maxUtility = 0 - 1000
        makeMove = 'null'

        northUtility = self.valueIterationDictionary[northNeighbour]
        southUtility = self.valueIterationDictionary[southNeighbour]
        eastUtility = self.valueIterationDictionary[eastNeighbour]
        westUtility = self.valueIterationDictionary[westNeighbour]


        ''' --- Policies --- '''
        # Probability values taken from the lectures

        if Directions.NORTH in legal:
            north = ((0.8 * northUtility) + (0.1 * westUtility) + (0.1 * eastUtility))
            if north > maxUtility:
                maxUtility = north
                makeMove = Directions.NORTH
                self.addLastPosition(makeMove,pacmanPos)

        if Directions.SOUTH in legal:
            south = ((0.8 * southUtility) + (0.1 * westUtility) + (0.1 * eastUtility))
            if south > maxUtility:
                maxUtility = south
                makeMove = Directions.SOUTH
                self.addLastPosition(makeMove, pacmanPos)

        if Directions.EAST in legal:
            east = ((0.8 * eastUtility) + (0.1 * northUtility) + (0.1 * southUtility))
            if east > maxUtility:
                maxUtility = east
                makeMove = Directions.EAST
                self.addLastPosition(makeMove, pacmanPos)

        if Directions.WEST in legal:
            west = ((0.8 * westUtility) + (0.1 * northUtility) + (0.1 * southUtility))
            if west > maxUtility:
                maxUtility = west
                makeMove = Directions.WEST
                self.addLastPosition(makeMove, pacmanPos)

        if makeMove != 'null':
            self.valueIterationStart = 0
            return api.makeMove(makeMove, legal)
            self.addLastPosition(makeMove, pacmanPos)

        else:
            print "error"