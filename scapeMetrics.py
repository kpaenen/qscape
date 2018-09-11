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

class SpatialCalculator(object):
    def __init__(self, ViewshedBinary, ViewshedClasses):
        self.vsBool = ViewshedBinary
        self.vsClasses = ViewshedClasses
        self.area = np.sum(self.vsBool)
    
    # Openness - input is boolean viewshed array
    def calcPerimeter():
        # sums sides of boolean raster
        a = self.vsBool
        return np.sum(a[:,1:] != a[:,:-1]) + np.sum(a[1:,:] != a[:-1,:])

    def perimAreaRatio():
        return calcPerimeter() / self.area

    def shapeIndex():
        ''' 
        normalised perimeter/area ratio
        index 1 = non-complex
        index > 1 = increasing complexity
        '''
        perimeter = calcPerimeter()
        return (0.25 * perimeter) / math.sqrt(self.area)

    def fractalDimension():
        ''' 
        normalised perimeter/area ratio independent of raster size
        index 1 = non-complex
        index 2 = maximal complexity 
        '''
        perimeter = calcPerimeter()
        return (2 * math.log(0.25 * perimeter)) / math.log(self.area)

    # Homogeneity - input is thematic viewshed array
    def getAbs():
        return np.unique(self.vsClasses) - 1

    def getFractions():
        fractions = []
        unique, counts = np.unique(self.vsClasses, return_counts = True)
        for i in counts[1:]:
            fractions.append(i/self.area)
        return fractions
        
    def calcSimpson():
        index = 0
        fractions = getFractions()
        for i in fractions:
            index += i*i
        return 1 - index

    def calcShannon():
        index = 0
        fractions = getFractions()
        for i in fractions:
            index -= i * math.log(i)
        return index

    # Complexity

