import numpy as np
import pandas
import networkx as nx
import json
from alns.Vehicle import Vehicle
from alns.TimeInterval import TimeInterval
from alns.Depot import Depot
from alns.PlaningHorizon import PlanningHorizon
from alns.ServiceStop import ServiceStop

class Problem:

    def __init__(self, instanceFilePath):

        depots, demand, fleet, timeMatrix, distanceMatrix, lunchBreak, lunchDuration = self.readInstance(instanceFilePath)

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

    
    @property
    def depots(self):
        return self._depot
    
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


    def readInstance(self, instanceFilepath):

        data = pandas.read_csv(instanceFilepath + "Data_1.csv")
        dataAsList = data.values.tolist()
        problemDescription = dataAsList[0]

        numVehicles = problemDescription[0]
        numStops = problemDescription[1]
        numDepots = problemDescription[2]
        lunchStart = problemDescription[3]
        lunchEnd = problemDescription[3]
        lunchDuration = problemDescription[4]

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
            row+=1
            newVehicle = Vehicle(set(skillSet), overtimeTreshhold, maxOvertime)
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
            
            prio = stopDataRow[column]
            lat = stopDataRow[column + 1]
            lng = stopDataRow[column + 2]
            serviceDuration = stopDataRow[column + 3]
            earliestService = stopDataRow[column + 4]
            latestService = stopDataRow[column + 5]
            row+=1
            newServiceStop = ServiceStop(nodeIndex, lat, lng, serviceDuration, PlanningHorizon(0, 0, 0), TimeInterval(earliestService, latestService),prio, set(skillsReq))
            listOfServiceStops.append(newServiceStop)
            nodeIndex+=1
            j+=1
        
        distanceMatrix = []
        timeMatrix = []
        with open(instanceFilepath + "Matrix_1.json") as json_file:
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
        pass
    
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
        print(max)
        return max


    def plot(self):
        pass


p = Problem("/Users/christophbleyer/Technician-Vehicle-Routing-Optimization/examples/Datasets/")