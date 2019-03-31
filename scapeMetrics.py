# -*- coding: utf-8 -*-
"""
/***************************************************************************
QScape
A QGIS plugin for generating a structural landscape classification map.
                             -------------------
       begin                : 2018-05-24
       git sha              : $Format:%H$
       copyright            : (C) 2018 by Killian Paenen
       email                : kpaenen@vub.be
***************************************************************************/

/***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************/
"""

import math
import numpy as np
import numpy_indexed as npi

class SpatialCalculator(object):
    def __init__(self, ViewshedBinary, ViewshedClasses):
        self.vsBool = ViewshedBinary
        self.vsClasses = ViewshedClasses
        self.area = np.sum(self.vsBool)
        self.rows = len(self.vsBool)
        self.cols = len(self.vsBool[0])   
    
    # Openness - input is boolean viewshed array
    ## Size
    def calcSize(self, x):
        # Caller function to handle radiobutton
        if x == 1: return self.area
        elif x == 2: return self.calcCore()
        else: return self.calcCoreIndex()
    
    def calcCore(self):
        # Generates largest possible square from centre location
        x = self.vsBool
        # Get indices at centre location
        halfRow = int((self.rows/2) - 1)
        halfCol = int((self.cols/2) - 1)
        contin = True
        core, count = 1, 1
        if x[halfRow][halfCol] == 0:
            return core
        else: 
            while contin:
                # If no 0 in neighbouring area, increment length
                if 0 not in x[halfRow-count:halfRow+count+1, halfCol-count:halfRow+count+1]:
                    core += 2
                    count += 1
                else: contin = False
            return core*core

    ''' # DEPRECATED
    def calcCore(self):
        # initiate
        current_col = [0]*(self.rows + 1)
        prev_col = [0]*(self.rows + 1)
        core = 0
        
        # find max core length possible per cell
        for j in range(self.cols-1, -1, -1):
            prev_col = current_col
            current_col = [0]*(self.rows + 1)
        
            for i in range(self.rows-1, -1, -1):
                if self.vsBool[i][j] == 1:
                    current_col[i] = min(current_col[i+1], prev_col[i], prev_col[i+1]) + 1
                    if current_col[i] > core:
                        core = current_col[i]
                else:
                    current_col[i] = 0
        return core*core
    '''
    
    def calcCoreIndex(self):
        core = self.calcCore()
        core *= core
        return core / self.area
    
    ## Shape
    def calcShape(self, x):
        # Caller function to handle radiobutton
        if x == 1: return self.calcPerimAreaRatio()
        elif x == 2: return self.calcShapeIndex()
        else: return self.calcFractalDimension()
        
    def calcPerimeter(self):
        # sums sides of boolean raster
        a = self.vsBool
        return np.sum(a[:,1:] != a[:,:-1]) + np.sum(a[1:,:] != a[:-1,:])

    def calcPerimAreaRatio(self):
        return self.calcPerimeter() / self.area

    def calcShapeIndex(self):
        ''' 
        normalised perimeter/area ratio
        index 1 = non-complex
        index > 1 = increasing complexity
        '''
        perimeter = self.calcPerimeter()
        return (0.25 * perimeter) / math.sqrt(self.area)

    def calcFractalDimension(self):
        ''' 
        normalised perimeter/area ratio independent of raster size
        index 1 = non-complex
        index 2 = maximal complexity 
        '''
        perimeter = self.calcPerimeter()
        return (2 * math.log(0.25 * perimeter)) / math.log(self.area)

    # Heterogeneity - input is thematic viewshed array
    def calcHetero(self, x):
        # Caller function to handle radiobutton
        if x == 1: return self.getAbs()
        elif x == 2: return self.calcSimpson()
        else: return self.calcShannon()
    
    def getAbs(self):
        # Get absolute number of classes
        return len(np.unique(self.vsClasses[self.vsClasses != 0]))

    def getFractions(self):
        fractions = []
        unique, counts = np.unique(self.vsClasses[self.vsClasses != 0], return_counts = True)
        for i in counts:
            fractions.append(i/self.area)
        return fractions
        
    def calcSimpson(self):
        index = 0
        fractions = self.getFractions()
        for i in fractions:
            index += i*i
        return 1 - index

    def calcShannon(self):
        index = 0
        fractions = self.getFractions()
        for i in fractions:
            index -= i * math.log(i)
        return index

    # Complexity - input is thematic viewshed array
    def calcComplex(self, x):
        # Caller function to handle radiobutton
        if x == 1: return self.calcAlternation()
        else: return self.calcContagion()
        
    def calcAlternation(self):
        a = self.vsClasses
        classes = self.getAbs()
        count = 0
        
        # Find islands per land cover class
        for cl in range(1, classes+1):
            
            for i in range(self.rows):
                for j in range(self.cols):
                    if a[i][j] == cl:
                        if ((i == 0 or a[i-1][j] != cl) and 
                            (j == 0 or a[i][j-1] != cl)):
                            count += 1
        return count
    
    def calcContagion(self):
        '''
        Contagion or edge density
        index 0 = maximum spatial complexity
        index 1 = no spatial complexity
        '''
        x = self.vsClasses
        fractions = self.getFractions()
        fracCount = 0
        index = 0
        
        # concatenate shifts to compare
        neighbours = np.concatenate([x[:, :-1].flatten(), 
                                     x[:, +1:].flatten(), 
                                     x[+1:, :].flatten(), 
                                     x[:-1, :].flatten(),
                                     x[:-1, :-1].flatten(),
                                     x[+1:, +1:].flatten(),
                                     x[:-1, +1:].flatten(),
                                     x[+1:, :-1].flatten()])

        centers   = np.concatenate([x[:, +1:].flatten(), 
                                    x[:, :-1].flatten(), 
                                    x[:-1, :].flatten(), 
                                    x[+1:, :].flatten(),
                                    x[+1:, +1:].flatten(),
                                    x[:-1, :-1].flatten(),
                                    x[+1:, :-1].flatten(),
                                    x[:-1, +1:].flatten()])
        
        # extract classes and count differences i.e. adjacencies  
        classes, neighboursPerClass = npi.group_by(centers, neighbours)
        for classID, neigh in zip(classes, neighboursPerClass):
            # skip class 0    
            if classID != 0:
                # count adjacencies, except those next to 0
                uniqueNeighbours, neighbourCounts = npi.count(neigh[neigh != 0])               
                for i in range(len(neighbourCounts)):
                    indTemp = fractions[fracCount] * (neighbourCounts[i] / np.sum(neighbourCounts))
                    index += indTemp * math.log(indTemp)
                fracCount += 1

        try:
            index /= (2 * math.log(self.getAbs()))
            index += 1
        except ZeroDivisionError:
            index = 1.
        return index
    