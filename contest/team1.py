
from captureAgents import CaptureAgent
import random, time, util, math
from game import Directions
from random import randint
from util import nearestPoint
#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first = 'ExploitationAgent', second = 'ExploitationAgent'):
  """
  This function should return a list of two agents that will form the
  team, initialized using firstIndex and secondIndex as their agent
  index numbers.  isRed is True if the red team is being created, and
  will be False if the blue team is being created.

  As a potentially helpful development aid, this function can take
  additional string-valued keyword arguments ("first" and "second" are
  such arguments in the case of this function), which will come from
  the --redOpts and --blueOpts command-line arguments to capture.py.
  For the nightly contest, however, your team will be created without
  any extra arguments, so you should make sure that the default
  behavior is what you want for the nightly contest.
  """

  # The following line is an example only; feel free to change it.
  return [eval(first)(firstIndex), eval(second)(secondIndex)]

##########
# Agents #
##########

class ReflexCaptureAgent(CaptureAgent):
  """
  A base class for reflex agents that chooses score-maximizing actions
  """

  def registerInitialState(self, gameState):
    self.start = gameState.getAgentPosition(self.index)

    #initialize food tracking for our food.
    self.startFood_team = self.getFoodYouAreDefending(gameState)
    self.carriedFood_team = self.startFood_team

    #initialize food tracking for enemy food.
    self.startFood_enemy = self.getFood(gameState)
    self.carriedFood_enemy = self.startFood_enemy

    self.midWidth = gameState.data.layout.width/2
    self.midHeight = gameState.data.layout.height/2
    while gameState.data.layout.walls[self.midWidth][self.midHeight]:
        print "moving mid"
        self.midHeight+=randint(-1,1)

    self.recentDeath = 0
    self.safetySwitch = 0

    CaptureAgent.registerInitialState(self, gameState)

  def chooseAction(self, gameState):
    """
    Picks among the actions with the highest Q(s,a).
    """
    actions = gameState.getLegalActions(self.index)

    # You can profile your evaluation time by uncommenting these lines
    # start = time.time()
    values = [self.evaluate(gameState, a) for a in actions]
    # print 'eval time for agent %d: %.4f' % (self.index, time.time() - start)

    maxValue = max(values)
    bestActions = [a for a, v in zip(actions, values) if v == maxValue]

    foodLeft = len(self.getFood(gameState).asList())

    if foodLeft <= 2:
      bestDist = 9999
      for action in actions:
        successor = self.getSuccessor(gameState, action)
        pos2 = successor.getAgentPosition(self.index)
        dist = self.getMazeDistance(self.start,pos2)
        if dist < bestDist:
          bestAction = action
          bestDist = dist
      return bestAction

    return random.choice(bestActions)

  def getSuccessor(self, gameState, action):
    """
    Finds the next successor which is a grid position (location tuple).
    """
    successor = gameState.generateSuccessor(self.index, action)
    pos = successor.getAgentState(self.index).getPosition()
    if pos != nearestPoint(pos):
      # Only half a grid position was covered
      return successor.generateSuccessor(self.index, action)
    else:
      return successor

  def evaluate(self, gameState, action):
    """
    Computes a linear combination of features and feature weights
    """
    features = self.getFeatures(gameState, action)
    weights = self.getWeights(gameState, action)
    return features * weights

  def getFeatures(self, gameState, action):
    """
    Returns a counter of features for the state
    """

    features = util.Counter()
    successor = self.getSuccessor(gameState, action)
    features['successorScore'] = self.getScore(successor)
    return features

  def getWeights(self, gameState, action):
    """
    Normally, weights do not depend on the gamestate.  They can be either
    a counter or a dictionary.
    """
    return {'successorScore': 1.0}


  #distancer = Distancer(gameState.data.layout)
  #distancer.getDistance((1, 1), (10, 10))

  # ===========================================================================================
  #======================================ADVANCED FEATURES=====================================
  # ===========================================================================================

  def isSafe(self, gameState, myPos, foodList):
      safetyThresh = 1.5
      enemyDist = self.getEnemyDistances(gameState)
      closestFood = min([self.getMazeDistance(myPos, food) for food in foodList])
      if enemyDist[0] > safetyThresh * closestFood and enemyDist[1] > safetyThresh * closestFood:
          canGetFood = True
      else:
          canGetFood = False
      return canGetFood


  def campCapsule(self, position, successor):

      capLocations = self.getCapsulesYouAreDefending(successor)
      capDistances = 0

      if len(capLocations) > 0:
          for cx, cy in capLocations:
              capDistances = self.getMazeDistance(position, (cx, cy))

      if len(capLocations) > 1:
          if self.index == 0 or self.index == 1:
              capDistances = self.getMazeDistance(position, capLocations[0])
          else:
              capDistances = self.getMazeDistance(position, capLocations[1])

      return capDistances


  def stayTowardMiddle(self, gameState, myPos):
    distToMiddle = abs(myPos[0] - self.midWidth)
    middleValue = 0
    if self.red:
      if myPos[0] <= self.midWidth:
        middleValue = self.getMazeDistance(myPos, (self.midWidth, self.midHeight)) / 4
        # middleValue = distToMiddle/4
      elif myPos[0] > self.midWidth:
        middleValue = 300
    else:
      if myPos[0] >= self.midWidth:
        middleValue = self.getMazeDistance(myPos, (self.midWidth, self.midHeight)) / 4
        # middleValue = distToMiddle/4
      elif myPos[0] < self.midWidth:
        middleValue = 300

    return middleValue


  def enemyRecentlyDied(self, gameState):
     if gameState.data.timeleft < 1196:
        previous = self.getPreviousObservation()
        o = self.getEnemyDistances(previous)
        c = self.getEnemyDistances(gameState)
        for index in range(len(o)):
            print c[index] - o[index]


  def getEnemyDistances(self, gameState):
    if self.red:
      enemyDist = [gameState.agentDistances[i] for i in range(len(gameState.teams)) if i % 2 == 0]
    else:
      enemyDist = [gameState.agentDistances[i] for i in range(len(gameState.teams)) if i % 2 == 1]
    return enemyDist

  #TODO Make it so that they are no longer carrying when scored
  def isEnemyCarrying(self, gameState):
      currentFood = self.getFoodYouAreDefending(gameState)
      #If they are killed or capture the dots, reset the food tracker
      if sum(x.count(1) for x in currentFood.data) > sum(x.count(1) for x in self.carriedFood_team.data):
        self.startFood_team = currentFood
        self.carriedFood_team = currentFood
        self.recentDeath = 1
        print "They dropped our food"
      #If there is less defended food than the start or last reset
      if sum(x.count(1) for x in currentFood.data) < sum(x.count(1) for x in self.startFood_team.data):
        self.carriedFood_team = currentFood
        return 1
      return 0

  def isTeamCarrying(self, gameState):
      currentFood = self.getFood(gameState)
      #If they are killed or capture the dots, reset the food tracker
      if sum(x.count(1) for x in currentFood.data) > sum(x.count(1) for x in self.carriedFood_enemy.data):
        self.startFood_enemy = currentFood
        self.carriedFood_enemy = currentFood
        self.recentDeath = 0
        print "We dropped their food"
      #If there is less defended food than the start or last reset
      if sum(x.count(1) for x in currentFood.data) < sum(x.count(1) for x in self.startFood_enemy.data):
        self.carriedFood_enemy = currentFood
        self.safetySwitch = 0
        return 1
      return 0


#----------------------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------------

class ExploitationAgent(ReflexCaptureAgent):
  """
  A reflex agent that keeps its side Pacman-free. Again,
  this is to give you an idea of what a defensive agent
  could be like.  It is not the best or only way to make
  such an agent.
  """

  def getFeatures(self, gameState, action):
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)

    myState = successor.getAgentState(self.index)
    myPos = myState.getPosition()

    #self.enemyRecentlyDied(gameState)

    # Computes whether we're on defense (1) or offense (0)
    features['onDefense'] = 1
    #if self.isEnemyCarrying(gameState): features['onDefense'] = 0
    #if myState.isPacman: features['onDefense'] = 0



    # Compute distance to the nearest food
    foodList = self.getFood(successor).asList()
    if len(foodList) > 0:  # This should always be True,  but better safe than sorry
        myPos = successor.getAgentState(self.index).getPosition()
        minDistance = min([self.getMazeDistance(myPos, food) for food in foodList])
        features['distanceToFood'] = minDistance


    # Computes distance to invaders we can see
    enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
    invaders = [a for a in enemies if a.isPacman and a.getPosition() != None]
    features['numInvaders'] = len(invaders)
    if len(invaders) > 0:
      dists = [self.getMazeDistance(myPos, a.getPosition()) for a in invaders]
      features['invaderDistance'] = min(dists)

    if action == Directions.STOP: features['stop'] = 1
    rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
    if action == rev: features['reverse'] = 1

    features['successorScore'] = -len(foodList)#self.getScore(successor)

    features['middleDistance'] = self.stayTowardMiddle(gameState, myPos)

    features['enemyDistance'] = min(self.getEnemyDistances(gameState))

    features['capsuleCamp'] = self.campCapsule(myPos, gameState)

    self.safe = self.isSafe(gameState, myPos, foodList)
    if self.safe:
        self.safetySwitch = 1

    self.enemyCarrying = self.isEnemyCarrying(gameState)
    self.teamCarrying = self.isTeamCarrying(gameState)

    return features

  def getWeights(self, gameState, action):

      #Switch distance to food based on if they are recently dead
      #if self.safetySwitch:
      if self.recentDeath:
          campSwitch = 0
      else:
          campSwitch = 1

      if self.teamCarrying:
          self.recentDeath = 0

      #TODO Make sure code will work for either teams
      #use binary switches to turn weights on and off
      return {'successorScore':-100 * (campSwitch-1),
              'distanceToFood':1 * (campSwitch-1),
              'numInvaders': -100,
              'onDefense': 10 * (self.teamCarrying+1),
              'invaderDistance': -10 * self.enemyCarrying,
              'stop': -100,
              'reverse': -2,
              'middleDistance': -0.25 * campSwitch,
              'enemyDistance': -.5,
              'capsuleCamp': -.25 * campSwitch}

#----------------------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------------

class OffensiveReflexAgent(ReflexCaptureAgent):
  """
  A reflex agent that seeks food. This is an agent
  we give you to get an idea of what an offensive agent might look like,
  but it is by no means the best or only way to build an offensive agent.
  """
  def getFeatures(self, gameState, action):
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)
    foodList = self.getFood(successor).asList()
    features['successorScore'] = -len(foodList)#self.getScore(successor)

    # Compute distance to the nearest food
    if len(foodList) > 0: # This should always be True,  but better safe than sorry
      myPos = successor.getAgentState(self.index).getPosition()
      minDistance = min([self.getMazeDistance(myPos, food) for food in foodList])
      features['distanceToFood'] = minDistance
    return features

  def getWeights(self, gameState, action):
    return {'successorScore': 100, 'distanceToFood': -1}

#----------------------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------------

class DefensiveReflexAgent(ReflexCaptureAgent):
  """
  A reflex agent that keeps its side Pacman-free. Again,
  this is to give you an idea of what a defensive agent
  could be like.  It is not the best or only way to make
  such an agent.
  """

  def getFeatures(self, gameState, action):
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)

    myState = successor.getAgentState(self.index)
    myPos = myState.getPosition()

    # Computes whether we're on defense (1) or offense (0)
    features['onDefense'] = 1
    if myState.isPacman: features['onDefense'] = 0

    # Computes distance to invaders we can see
    enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
    invaders = [a for a in enemies if a.isPacman and a.getPosition() != None]
    features['numInvaders'] = len(invaders)
    if len(invaders) > 0:
      dists = [self.getMazeDistance(myPos, a.getPosition()) for a in invaders]
      features['invaderDistance'] = min(dists)

    if action == Directions.STOP: features['stop'] = 1
    rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
    if action == rev: features['reverse'] = 1

    return features

  def getWeights(self, gameState, action):
    return {'numInvaders': -1000, 'onDefense': 100, 'invaderDistance': -10, 'stop': -100, 'reverse': -2}

# ----------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------


class DummyAgent(CaptureAgent):
  """
  A Dummy agent to serve as an example of the necessary agent structure.
  You should look at baselineTeam.py for more details about how to
  create an agent as this is the bare minimum.
  """

  def registerInitialState(self, gameState):
    """
    This method handles the initial setup of the
    agent to populate useful fields (such as what team
    we're on).

    A distanceCalculator instance caches the maze distances
    between each pair of positions, so your agents can use:
    self.distancer.getDistance(p1, p2)

    IMPORTANT: This method may run for at most 15 seconds.
    """

    '''
    Make sure you do not delete the following line. If you would like to
    use Manhattan distances instead of maze distances in order to save
    on initialization time, please take a look at
    CaptureAgent.registerInitialState in captureAgents.py.
    '''
    CaptureAgent.registerInitialState(self, gameState)

    '''
    Your initialization code goes here, if you need any.
    '''


  def chooseAction(self, gameState):
    """
    Picks among actions randomly.
    """
    actions = gameState.getLegalActions(self.index)

    '''
    You should change this in your own agent.
    '''

    return random.choice(actions)

#----------------------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------------

