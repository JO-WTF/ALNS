import numpy as np
import pandas
import networkx as nx
import matplotlib.pyplot as plt
import json
from .Vehicle import Vehicle
from .TimeInterval import TimeInterval
from .Depot import Depot
from .PlaningHorizon import PlanningHorizon
from .ServiceStop import ServiceStop
from .Route import Route
from operators import *
from construction import Construction

class Problem:

    def __init__(self, instanceFilePath, routingDataFilePath):

        depots, demand, fleet, timeMatrix, distanceMatrix, lunchBreak, lunchDuration = self.readInstance(instanceFilePath, routingDataFilePath)

        self._depots = depots
        self._demand = demand
        self._fleet = fleet
        self._timeMatrix = timeMatrix
        self._distanceMatrix = distanceMatrix
        self._lunchBreak = lunchBreak
        self._lunchDuration = lunchDuration

        self._serviceMap = self.buildServiceMap()
        self._maxServiceStartDistance = self.calculateMaxServiceStartDistance()
        self._maxTravelTimeOccurences = self.calculcateMaxTravelTimeOccurences()
        self._maxTimeWindowDistance = self.calculateMaxTimeWindowDistance()
        self._maxTimeWindowLength =  self.calculateMaxTimeWindowLength()
        self._maxServiceTime = self.calculateMaxServiceTime()
        self._avgDrivingCost = 0.0001

    
    @property
    def maxServiceTime(self):
        return self._maxServiceTime


    @property
    def maxTimeWindowLength(self):
        return self._maxTimeWindowLength

    @property
    def depots(self):
        return self._depots
    
    @property
    def demand(self):
        return self._demand
    
    @property
    def fleet(self):
        return self._fleet
    
    @property
    def timeMatrix(self):
        return self._timeMatrix

    @property
    def distanceMatrix(self):
        return self._distanceMatrix

    @property
    def lunchBreak(self):
        return self._lunchBreak                      
    
    @property
    def lunchDuration(self):
        return self._lunchDuration
    
    @property
    def serviceMap(self):
        return self._serviceMap
    
    @property
    def maxServiceStartDistance(self):
        return self._maxServiceStartDistance
    
    @property
    def maxTravelTimeOccurences(self):
        return self._maxTravelTimeOccurences
    
    @property
    def maxTimeWindowDistance(self):
        return self._maxTimeWindowDistance
    
    @property
    def avgDrivingCost(self):
        return self._avgDrivingCost
    

    # Read an instance from the local disk
    def readInstance(self, instanceFilepath, routingDataFilePath):

        data = pandas.read_csv(instanceFilepath)
        dataAsList = data.values.tolist()
        problemDescription = dataAsList[0]

        numVehicles = problemDescription[0]
        numStops = problemDescription[1]
        numDepots = problemDescription[2]
        lunchStart = problemDescription[3]
        lunchEnd = problemDescription[4]
        lunchDuration = problemDescription[5]

        lunchbreak = TimeInterval(lunchStart, lunchEnd)

        row = 1

        listOfVehicles = []
        while(row <= numVehicles):
            vehicleDataRow = dataAsList[row]
            numSkills = vehicleDataRow[1]
            
            skillSet = []
            column = 2
            i = 0
            while(i < numSkills):
                skillSet.append(vehicleDataRow[column])
                i+=1
                column+=1
            
            overtimeTreshhold = vehicleDataRow[column]
            maxOvertime = vehicleDataRow[column + 1]
            overTimeCost = vehicleDataRow[column + 2]
            row+=1
            newVehicle = Vehicle(set(skillSet), overtimeTreshhold, maxOvertime, overTimeCost)
            listOfVehicles.append(newVehicle)
        
        nodeIndex = 0

        listOfDepots = []
        j = 0
        while(j < numDepots):
            depotDataRow = dataAsList[row]
            numVehicles = depotDataRow[1]
            
            vehicles = []
            column = 2
            i = 0
            while(i < numVehicles):
                vehicles.append(listOfVehicles[int(depotDataRow[column])])
                i+=1
                column+=1

            lat = depotDataRow[column]
            lng = depotDataRow[column + 1]
            row+=1
            
            # magic numbers: A depot can be visited any time across the 24 hour planning horzion.
            newDepot = Depot(nodeIndex, lat, lng, 0, PlanningHorizon(0,0,0), TimeInterval(0, 86400), vehicles)
            listOfDepots.append(newDepot)
            nodeIndex+=1
            j+=1
        
        
        
        listOfServiceStops = []
        j = 0
        while(j < numStops):
            stopDataRow = dataAsList[row]
            numSkillReq = stopDataRow[1]
        
            skillsReq = []
            column = 2
            i = 0
            while(i < numSkillReq):
                skillsReq.append(stopDataRow[column])
                i+=1
                column+=1
            
            lat = stopDataRow[column + 1]
            lng = stopDataRow[column + 2]
            serviceDuration = stopDataRow[column + 3]
            earliestService = stopDataRow[column + 4]
            latestService = stopDataRow[column + 5]
            profitForcast = stopDataRow[column + 6]
            row+=1
            newServiceStop = ServiceStop(nodeIndex, lat, lng, serviceDuration, PlanningHorizon(0, 0, 0), TimeInterval(earliestService, latestService), set(skillsReq), profitForcast)
            listOfServiceStops.append(newServiceStop)
            nodeIndex+=1
            j+=1
        
        distanceMatrix = []
        timeMatrix = []
        with open(routingDataFilePath) as json_file:
            matrixData = json.load(json_file)
            distanceMatrix = np.matrix(matrixData["distances"])
            timeMatrix = np.matrix(matrixData["durations"])

        return listOfDepots, listOfServiceStops, listOfVehicles, timeMatrix, distanceMatrix, lunchbreak, lunchDuration

    def buildServiceMap(self):
        serviceMap = {}
        for stop in self.demand:
            serviceMap[stop.index] = []
            for vehicle in self.fleet:
                if vehicle.canServe(stop):
                    serviceMap[stop.index].append(vehicle)
        return serviceMap


    def calculcateMaxTravelTimeOccurences(self):
       customersOnly = self._timeMatrix[len(self.depots):,len(self.depots):]
       sortedAsList = np.sort(customersOnly.ravel()).tolist()[0]
       biggestTwo = sortedAsList[len(sortedAsList) - 2:]
       return biggestTwo
    
    def calculateMaxServiceStartDistance(self):
        max = -1
        i = 0
        # the temporal distance is a symmetric measure
        while(i < len(self._demand)):
            j = 0
            while(j < len(self._demand)):
                if i < j:
                    temporalDistance = self._demand[i].getServiceTimeStartDistance(self._demand[j])
                    if temporalDistance > max:
                        max = temporalDistance
                j+=1
            i+=1
        return max
    
    def calculateMaxTimeWindowLength(self):
        twlenghts = []
        for cust in self.demand:
            twLength = cust.serviceTime.latest - cust.serviceTime.earliest
            twlenghts.append(twLength)
        
        maximum = max(twlenghts)
        return maximum
    
    def calculateMaxServiceTime(self):
        serviceTimes = []
        for cust in self.demand:
            serviceTimes.append(cust.serviceDuration)
        
        maximum = max(serviceTimes)
        return maximum
        
    
    def calculateMaxTimeWindowDistance(self):
        # Depots are excluded since they are always 0 in distance since their time windows are nested
        max = -1
        i = 0
        # the tw distance is a symmetric measure.
        while(i < len(self._demand)):
            j = 0
            while(j < len(self._demand)):
                if i <=j:
                    twDistance = Construction.tansiniDTW(self._demand[i], self._demand[j])
                    if twDistance > max:
                        max = twDistance
                j+=1
            i+=1
        return max

    def plot(self):
        G = nx.DiGraph(directed=True)
        colors = []
        labels = {}
        for depot in self._depots:
            G.add_node(depot.index, pos=(depot.lng, depot.lat))
            colors.append('blue')
        
        for stop in self._demand:
            G.add_node(stop.index, pos=(stop.lng, stop.lat))
            colors.append('orange')
        
        nx.draw(G, nx.get_node_attributes(G, 'pos'), node_color=colors, with_labels=True)
        return G



