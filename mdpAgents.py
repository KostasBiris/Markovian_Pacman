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

# Solution by Konstantinos Biris [k21187367]

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


    def gameMap(self, state):
        # Map of all static objects, namely food, capsules and walls.
        stageMap = []

        # Values Map used to assign values to all the different positions/states on the map.
        self.valuesMap = {}

        foodPos = api.food(state)
        capsulePos = api.capsules(state)

        wallPos = api.walls(state)
        mapCornerPos = api.corners(state)

        # Get the size of the map
        biggestX = 0
        biggestY = 0
        for i in range(len(mapCornerPos)):
            if mapCornerPos[i][0] > biggestX: biggestX = mapCornerPos[i][0]
            if mapCornerPos[i][1] > biggestY: biggestY = mapCornerPos[i][1]

        self.mapWidth = biggestX + 1
        self.mapHeight = biggestY + 1

        # Build a map containing all the positions and their values/rewards
        for i in range(self.mapWidth):
            for j in range(self.mapHeight):
                if (i,j) not in wallPos:
                    self.valuesMap[(i, j)] = 0

        # Map of all positions that Pacman is allowed to go to.
        self.allowedPos = self.valuesMap.keys()

        # Initial Values assignment stage
        for f in foodPos: self.valuesMap[f] = 10
        for c in capsulePos: self.valuesMap[c] = 2


    def updateStaticObjValues(self, state):
        foodPos = api.food(state)
        capsulePos = api.capsules(state)
        ghostsRange = self.findGhostsRange(state)

        # Reset all the values
        for k in self.valuesMap.keys(): self.valuesMap[k] = -1

        # Assign a suitable value/reward to the position of each object
        for f in foodPos: self.valuesMap[f] = 10
        for c in capsulePos: self.valuesMap[c] = 2
        for h in ghostsRange[0]: self.valuesMap[h] = -500
        for s in ghostsRange[1]: self.valuesMap[s] = 200

    def valueIteration(self, state, ghostsRange):

        wallPos = api.walls(state)
        reward = -1  # value taken from lecture slides
        gamma = 0.9  # value taken from lecture slides

        # make a copy of the current (old) value iteration dictonary to compare it withe the new one later on.
        if self.valueIterationStart == 0:
            self.valueIterationDictionary = self.valuesMap.copy()
            self.valueIterationStart = 1
        temp = self.valueIterationDictionary.copy()

        # Assign rewards on the neighboring cells in order to calculate the utlity of their coordinates
        # using the Bellman Equation later on.
        for pos in self.allowedPos:
            reward = self.valuesMap[pos]
            northNeighbour = southNeighbour = eastNeighbour = westNeighbour = eastNeighbour = pos

            # North Coordinates
            if (pos[0], pos[1] + 1) not in wallPos:
                northNeighbour = (pos[0], pos[1] + 1)
            # South Coordinates
            if (pos[0], pos[1] - 1) not in wallPos:
                southNeighbour = (pos[0], pos[1] - 1)
            # East Coordinates
            if (pos[0] + 1, pos[1]) not in wallPos:
                eastNeighbour = (pos[0] + 1, pos[1])
            # West Coordinates
            if (pos[0] - 1, pos[1]) not in wallPos:
                westNeighbour = (pos[0] - 1, pos[1])



            # Bellman Equation implementation. Find the utility from the last iterated values
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
            self.valueIterationDictionary[pos] = round(valueIteration, 3)

        # This compares the old value iteration dictionary and the new one
        stability = cmp(temp, self.valueIterationDictionary)
        return stability


    # Find the Ghosts Range
    # This includes the position of each ghost and their surrounding cells.
    #
    # We have two separate lists:
    #   ghostsRange[0] has the ranges of all the Hostile Ghosts
    #   ghostsRange[1] has the ranges of all the Scared Ghosts
    def findGhostsRange(self, state):
        ghoststates = api.ghostStatesWithTimes(state)
        hostileGhostsRange = []
        scaredGhostsRange = []

        # Making a list of ghost coordinates and their surrounding cells
        for i in range(len(ghoststates)):
            # converting ghosts coordinates in integer
            ghostX = ghoststates[i][0][0]
            ghostY = ghoststates[i][0][1]

            # Current ghost position
            ghostPos = (int(ghostX), int(ghostY))

            if ghostPos in self.allowedPos:
                # Add Current Ghost Position to the Ghost Range
                if ghoststates[i][1] <= 4: hostileGhostsRange.append(ghostPos)
                else: scaredGhostsRange.append(ghostPos)

                # Add the position North of the Ghost to the Ghost Range
                if ghoststates[i][1] <= 4: hostileGhostsRange.append((ghostPos[0], ghostPos[1] + 1))
                else: scaredGhostsRange.append((ghostPos[0], ghostPos[1] + 1))
                # Add the position South of the Ghost to the Ghost Range
                if ghoststates[i][1] <= 4: hostileGhostsRange.append((ghostPos[0], ghostPos[1] - 1))
                else: scaredGhostsRange.append((ghostPos[0], ghostPos[1] - 1))
                # Add the position East of the Ghost to the Ghost Range
                if ghoststates[i][1] <= 4: hostileGhostsRange.append((ghostPos[0] + 1, ghostPos[1]))
                else: scaredGhostsRange.append((ghostPos[0] + 1, ghostPos[1]))
                # Add the position West of the Ghost to the Ghost Range
                if ghoststates[i][1] <= 4: hostileGhostsRange.append((ghostPos[0] - 1, ghostPos[1]))
                else: scaredGhostsRange.append((ghostPos[0] - 1, ghostPos[1]))

                # Add the position North-West of the Ghost to the Ghost Range
                if ghoststates[i][1] <= 4: hostileGhostsRange.append((ghostPos[0] - 1, ghostPos[1] + 1))
                else: scaredGhostsRange.append((ghostPos[0] - 1, ghostPos[1] + 1))
                # Add the position North-East of the Ghost to the Ghost Range
                if ghoststates[i][1] <= 4: hostileGhostsRange.append((ghostPos[0] + 1, ghostPos[1] + 1))
                else: scaredGhostsRange.append((ghostPos[0] + 1, ghostPos[1] + 1))
                # Add the position South-West of the Ghost to the Ghost Range
                if ghoststates[i][1] <= 4: hostileGhostsRange.append((ghostPos[0] - 1, ghostPos[1] - 1))
                else: scaredGhostsRange.append((ghostPos[0] - 1, ghostPos[1] - 1))
                # Add the position South-East of the Ghost to the Ghost Range
                if ghoststates[i][1] <= 4: hostileGhostsRange.append((ghostPos[0] + 1, ghostPos[1] - 1))
                else: scaredGhostsRange.append((ghostPos[0] + 1, ghostPos[1] - 1))

        return [hostileGhostsRange,scaredGhostsRange]


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

        # If the move is illegal, we keep the neighbor's position equal to Pacmans current position
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


        maxUtility = -1000
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

        if Directions.SOUTH in legal:
            south = ((0.8 * southUtility) + (0.1 * westUtility) + (0.1 * eastUtility))
            if south > maxUtility:
                maxUtility = south
                makeMove = Directions.SOUTH

        if Directions.EAST in legal:
            east = ((0.8 * eastUtility) + (0.1 * northUtility) + (0.1 * southUtility))
            if east > maxUtility:
                maxUtility = east
                makeMove = Directions.EAST

        if Directions.WEST in legal:
            west = ((0.8 * westUtility) + (0.1 * northUtility) + (0.1 * southUtility))
            if west > maxUtility:
                maxUtility = west
                makeMove = Directions.WEST

        if makeMove != 'null':
            self.valueIterationStart = 0
            return api.makeMove(makeMove, legal)

        # If Pacman gets surrounded he should stay still
        # and accept his fate (otherwise Illegal Move Exception)
        else:
            makeMove = Directions.STOP
            self.valueIterationStart = 0
            return api.makeMove(makeMove, legal)
