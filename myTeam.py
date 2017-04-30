# baselineTeam.py
# ---------------
# Licensing Information: Please do not distribute or publish solutions to this
# project. You are free to use and extend these projects for educational
# purposes. The Pacman AI projects were developed at UC Berkeley, primarily by
# John DeNero (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# For more info, see http://inst.eecs.berkeley.edu/~cs188/sp09/pacman.html

from captureAgents import CaptureAgent
import distanceCalculator
import random, time, util
from game import Directions
import game
from util import nearestPoint
from util import manhattanDistance


#################
# Team creation #
#################


def createTeam(firstIndex, secondIndex, isRed,
               first = 'OffensiveReflexAgent', second = 'DefensiveReflexAgent'):
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

  return [eval(first)(firstIndex), eval(second)(secondIndex)]

##########
# Agents #
##########

class ReflexCaptureAgent(CaptureAgent):
  """
  A base class for reflex agents that chooses score-maximizing actions
  """
  def chooseAction(self, gameState):
    """
    Picks among the actions with the highest Q(s,a).
    """
    actions = gameState.getLegalActions(self.index)
    #actions.remove(Directions.STOP)

    # You can profile your evaluation time by uncommenting these lines
    # start = time.time()
    values = [self.evaluate(gameState, a) for a in actions]
    # print 'eval time for agent %d: %.4f' % (self.index, time.time() - start)

    maxValue = max(values)
    bestActions = [a for a, v in zip(actions, values) if v == maxValue]

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
    #print gameState.getAgentState(self.index).getPosition()
    #print action
    #print features
    #print features * weights
    #print "---------------"
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

class OffensiveReflexAgent(ReflexCaptureAgent):
  """
  A reflex agent that seeks food. This is an agent
  we give you to get an idea of what an offensive agent might look like,
  but it is by no means the best or only way to build an offensive agent.
  """ 

  def getFeatures(self, gameState, action):
    
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)
    features['successorScore'] = self.getScore(successor)

    if action == Directions.STOP: features['stop'] = 1

    features['onAttack'] = 1
    if not successor.getAgentState(self.index).isPacman: features['onAttack'] = 0
    
    foodList = self.getFood(successor).asList()
    myPos = successor.getAgentState(self.index).getPosition()
  
    #calculate the closest enemy
    enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
    ghosts = [a for a in enemies if a.getPosition() != None] 
    minDistanceGhost = float("inf")
    closestEnemy = None
    for a in ghosts:
      if self.getMazeDistance(myPos, a.getPosition())< minDistanceGhost:
        closestEnemy = a
    #distance to the closest enemy    
    dists = [self.getMazeDistance(myPos, a.getPosition()) for a in ghosts]
    minDistanceGhost = float("inf")
    if len(dists)>0:
      minDistanceGhost = min(dists)

    enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
    enemiesOld = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
    closeEnemies = [a for a in enemies if a.getPosition() != None]
    invadersOld = [a for a in enemiesOld if a.isPacman and a.getPosition() != None]
    invaders = [a for a in enemies if a.isPacman and a.getPosition() != None]
    
    #the agent is a ghost
    if not successor.getAgentState(self.index).isPacman:      
      minDistance = min([self.getMazeDistance(myPos, food) for food in foodList])
      if myPos == gameState.getInitialAgentPosition(self.index):
        features['numInvaders'] = 2
      if len(invaders) < len(invadersOld):
            features['numPacman'] = -2 
      if len(closeEnemies)!=0 and minDistanceGhost < 6 and not successor.getAgentState(self.index).scaredTimer:
        dists = [self.getMazeDistance(myPos, a.getPosition()) for a in closeEnemies]
        if closeEnemies[0].isPacman:
          features['invaderDistance'] = min(dists)
          features['eatingPacman'] = 1
        else:
          features['invaderDistance'] = -min(dists)
        
        return features
      else:
        features['distanceToFood'] = minDistance         
        return features        

          
    else:  #the agent is pacman
      if gameState.getAgentState(self.index).configuration.direction == Directions.REVERSE[self.getPreviousObservation().getAgentState(self.index).configuration.direction]:
        if action == self.getPreviousObservation().getAgentState(self.index).configuration.direction:
          features['loop'] = 1
          return features

      #Noisy distance to the enemies 
      distEnemies = []
      dist = gameState.getAgentDistances()
      for i in self.getOpponents(successor):
        if not successor.getAgentState(i).isPacman:
          distEnemies.append(dist[i])
      if len(distEnemies) != 0:    
        noisyDist = min(distEnemies)  
      else:
         noisyDist = 0

      #distance to closest capsule
      red = gameState.isOnRedTeam(self.index)
      if red:
        capsules = successor.getBlueCapsules() 
        oldCapsules = gameState.getBlueCapsules()
      else:
        capsules = successor.getRedCapsules()
        oldCapsules = gameState.getRedCapsules()
        
      minDistanceCapsule = float("inf")
      closestCap = None
      for cap in capsules:
        tempDist = self.getMazeDistance(myPos, cap)
        if tempDist < minDistanceCapsule:
          minDistanceCapsule = tempDist
          closestCap = cap

      #Calculate distance to closest food 
      #distancesFood = [self.getMazeDistance(myPos, food) for food in foodList]
      #minDistanceFood = min(distancesFood)

      minDistanceFood = float("inf")
      closestFood = None
      for food in foodList:
        tempDist = self.getMazeDistance(myPos, food)
        if tempDist < minDistanceFood:
          minDistanceFood = tempDist
          closestFood = food

      #calculate distance to closest ghost enemy
      enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
      ghosts = [a for a in enemies if not a.isPacman and a.getPosition() != None] 
      minDistanceGhost = float("inf")
      for g in ghosts:
        tempDist = self.getMazeDistance(myPos, g.getPosition())
        if tempDist < minDistanceGhost:
          minDistanceGhost = tempDist
          closestGhost = g

      #if the closest enemy is pacman and is closer than 3  ####
      #if closestEnemy!= None and closestEnemy.isPacman and self.getMazeDistance(myPos, closestEnemy.getPosition())<3: 
      #   features['invaderDistance'] = self.getMazeDistance(myPos, closestEnemy.getPosition())
      #   return features

      # the closest ghost is scared
      for g in ghosts:
        if g.scaredTimer and self.getMazeDistance(myPos, g.getPosition()) == minDistanceGhost:
          features['distanceToFood'] = minDistanceFood
          if len(capsules) < len(oldCapsules): #eat the capsule
            features['numInvaders'] = -2
          return features

      #A ghost is chasing pacman 
      if minDistanceGhost <7:
        features['noGhost'] = 0
        if minDistanceGhost<=1: 
          features['distanceToFood'] = minDistanceFood
          features['numInvaders'] = 2
          return features  
        if len(capsules) < len(oldCapsules): #eat the capsule
          features['numInvaders'] = -2
        elif len(capsules) != 0:  #if there is any capsule in the map
          if minDistanceCapsule > self.getMazeDistance(closestCap,closestGhost.getPosition()):
            features['ghostDistance'] = minDistanceGhost #otherwise run away from the ghost 

          else:
            features['distanceToCapsule'] = minDistanceCapsule #go to the capsule if we are closer than the ghost
            features['successorScore'] = self.getScore(gameState)
            if minDistanceCapsule < self.getMazeDistance(closestCap,gameState.getAgentState(self.index).getPosition()):
              features['goForCapsule'] = 1
            return features

        if len(successor.getLegalActions(self.index))<3: # if the next square has no other exit
          x,y = successor.getAgentState(self.index).getPosition()
          if gameState.hasFood(int(x),int(y)):
            features['ghostDistance'] = minDistanceGhost
          else: #Don't go if there is no food in the square
            features['ghostDistance'] = -500  
        else:  #no capsules in the map and no dead paths
            features['ghostDistance'] = minDistanceGhost
            if minDistanceFood < self.getMazeDistance(closestFood,closestGhost.getPosition()):
              features['distanceToFood'] = minDistanceFood
              if minDistanceFood < self.getMazeDistance(closestFood,gameState.getAgentState(self.index).getPosition()):
                features['goForFood'] = 1
            else:  
              for food in foodList:
                if self.getMazeDistance(myPos, food) < self.getMazeDistance(food,closestGhost.getPosition()):
                  features['distanceToFood'] = self.getMazeDistance(myPos,food)
                  features['goForFood'] = 1
                  break
      #There is no ghost chasing pacman  

      else:
        #features['noisyDistance'] = noisyDist 
        features['noGhost'] = 1
        features['distanceToFood'] = minDistanceFood

      if len(successor.getLegalActions(self.index))<3: # if the next square has no other exit
          x,y = successor.getAgentState(self.index).getPosition()
          if gameState.hasFood(int(x),int(y)):
            features['ghostDistance'] = minDistanceGhost
          else: #Don't go if there is no food in the square
            features['ghostDistance'] = -500    

    # Compute distance to the nearest food
    #foodList = self.getFood(successor).asList()
    #if len(foodList) > 0: # This should always be True,  but better safe than sorry
    #  myPos = successor.getAgentState(self.index).getPosition()
    #
    #  print gameState.getRedCapsules()
    #
    #  minDistance = min([self.getMazeDistance(myPos, food) for food in foodList])
    #  features['distanceToFood'] = minDistance
    return features

  def getWeights(self, gameState, action):
    return {'stop':-1000,'numInvaders':-1000,'numPacman':-100, 'successorScore': 100, 'invaderDistance':-10, 'distanceToFood': -1, 'HomeDistance': -2, 'distanceToCapsule':-5, 'ghostDistance':5, 'noisyDistance':1, 'goForFood':50,'goForCapsule':100, 'loop':-300, 'noGhost':30, 'eatingPacman':65}

class DefensiveReflexAgent(ReflexCaptureAgent):
  """
  A reflex agent that keeps its side Pacman-free. Again,
  this is to give you an idea of what a defensive agent
  could be like. It is not the best or only way to make
  such an agent.
  """
  def getFeatures(self, gameState, action):

    features = util.Counter()
    successor = self.getSuccessor(gameState, action)

    myState = successor.getAgentState(self.index)
    myPos = myState.getPosition()

    if action == Directions.STOP: features['stop'] = 1


    # Computes whether we're on defense (1) or offense (0)
    features['onDefense'] = 1
    if myState.isPacman: features['onDefense'] = 0

    #number of enemies in our field
    enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
    inv = [a for a in enemies if a.isPacman]

    #closest food from their initial position
    foodList =  self.getFoodYouAreDefending(gameState).asList()

    minDistanceToFood = float("inf")
    initialPosition = gameState.getInitialAgentPosition(self.getOpponents(successor)[0])
    closestFood = None
    for food in foodList:
      tempDist = self.getMazeDistance(food,initialPosition)
      if tempDist < minDistanceToFood:
        minDistanceToFood = tempDist
        closestFood = food

    if len(inv) == 0:
      features['closestFood'] = self.getMazeDistance(myPos, closestFood)
      return features 

    # Computes distance to invaders we can see
    enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
    invaders = [a for a in enemies if a.isPacman and a.getPosition() != None]
    features['numInvaders'] = len(invaders)
    if len(invaders) > 0: #we can see the enemy
      dists = [self.getMazeDistance(myPos, a.getPosition()) for a in invaders]
      features['invaderDistance'] = min(dists)
      if len(inv) ==1 and len(gameState.getLegalActions(self.index))==3:
        blocked = 1
        for food in foodList:
          if self.getMazeDistance(myPos,food) > self.getMazeDistance(invaders[0].getPosition(),food):
            blocked = 0
        if blocked==1 and action == Directions.STOP and min(dists) <=2:
          features['numInvaders'] = -3
              


    else: #we can't see the enemy
      distEnemies = []

      dist = successor.getAgentDistances()
      dist2 = [0,0]
      if self.getPreviousObservation() != None:
        dist2 = self.getPreviousObservation().getAgentDistances()
      for i in self.getOpponents(successor):
        distEnemies.append((dist[i]+dist2[i])/2)
      features['noisyInvaderDistance'] = min(distEnemies) 
      if len(successor.getLegalActions(self.index))<3:# don't go into squares with no other exit
         features['noisyInvaderDistance'] = 30
      if self.getPreviousObservation() !=None:
        foodListOld =  self.getFoodYouAreDefending(self.getPreviousObservation()).asList()
        if len(foodList) < len(foodListOld):
          for food in foodListOld:
            if food not in foodList:
              for food2 in foodList:
                distFood = float("inf")
                nextFood = None
                d = self.getMazeDistance(food, food2)
                if d !=0 and d<distFood:
                  distFood = d
                  nextFood = food2
              features['invaderDistance'] = self.getMazeDistance(myPos,nextFood)
              features['noisyInvaderDistance'] = 0
        foodListNew =  self.getFoodYouAreDefending(successor).asList()      
        if len(foodListNew) < len(foodListOld):
          for food in foodListOld:
            if food not in foodListNew:
              for food2 in foodListNew:
                distFood = float("inf")
                nextFood = None
                d = self.getMazeDistance(food, food2)
                if d !=0 and d<distFood:
                  distFood = d
                  nextFood = food2
              features['invaderDistance'] = self.getMazeDistance(myPos,nextFood) 
              features['noisyInvaderDistance'] = 0

    rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
    if action == rev: features['reverse'] = 1

    return features

  def getWeights(self, gameState, action):
    return {'numInvaders': -1000, 'onDefense': 10, 'invaderDistance': -10, 'stop': -1000, 'reverse': -2, 'middle': -1, 'closestFood':-1, 'noisyInvaderDistance':-2}
