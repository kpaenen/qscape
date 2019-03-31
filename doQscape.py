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

from builtins import str, range

import os
from osgeo import gdal
from PyQt5 import uic
from PyQt5.QtCore import Qt, QFile, QFileInfo, QVariant
from PyQt5.QtWidgets import QDialog, QFileDialog, QInputDialog, QMessageBox, QTableWidgetItem
from qgis.core import (
    QgsProject,
    QgsPointXY,
    QgsRaster,
    QgsVectorLayer
)
import csv
import processing
from . import scapeMetrics

Ui_Dialog = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'qscapeUi.ui'))[0]

class Dialog(QDialog, Ui_Dialog):
        
    #TODO add items

    def __init__(self, iface):
        QDialog.__init__(self)
        self.iface = iface
        self.setupUi(self)
        # activate buttons etc
        self.outToolBut.clicked.connect(self.outFile)
        
        self.inRastCombo.clear()
        self.inDEMCombo.clear()
        layer_list = self.getLayers()
        self.inRastCombo.addItems(layer_list)
        self.inDEMCombo.addItems(layer_list)

    
    def outFile(self):
        # display dialog for output file
        self.outLineEdit.clear()
        outName, _ = QFileDialog().getSaveFileName(self, "Output file", ".", 
                                "Comma seperated values (*.csv);;Shapefiles (*.shp)",
                                options = QFileDialog.DontConfirmOverwrite)
        outPath = QFileInfo(outName).absoluteFilePath()
        if not outPath.upper().endswith('.CSV') and not outPath.upper().endswith('.SHP'):
            outPath += '.csv'
        if outName:
            self.outLineEdit.clear()
            self.outLineEdit.insert(outPath)

    def getLayers(self):
        # make layer list to display in combobox
        layers = [layer for layer in QgsProject.instance().mapLayers().values()]
        layer_list = []
        for layer in layers:
            layer_list.append(layer.name())
        return layer_list
        
    def rst(self, QRast):
        # transform QRaster Object to Numpy array
        Raster = gdal.Open(QRast)
        Band = Raster.GetRasterBand(1)
        Array = Band.ReadAsArray()
        return Array
    
    def checkMeasures(self):
        # check which measures
        # Openness - size
        if self.areaRadioBut.isChecked():
            SIZE_ID = 1
        else: SIZE_ID = 2
#            elif dlg.coreRadioBut.isChecked():
#                SIZE_ID = 2
#            else: SIZE_ID = 3
        # Openness - shape
        if self.ratioRadioBut.isChecked():
            SHAPE_ID = 1
        elif self.shapeRadioBut.isChecked():
            SHAPE_ID = 2
        else: SHAPE_ID = 3
        # Heterogeneity
        if self.absRadioBut.isChecked():
            HETERO_ID = 1
        elif self.simpsonRadioBut.isChecked():
            HETERO_ID = 2
        else: HETERO_ID = 3
        # Complexity
        if self.altRadioBut.isChecked():
            COMPLEX_ID = 1
        else: COMPLEX_ID = 2
        return SIZE_ID, SHAPE_ID, HETERO_ID, COMPLEX_ID
    
    def getViewClip(self, i, j, DEM, VIEW_ELEV, 
                    MAX_DIST, MEMORY, HALF_MAX, LCMap):
        # calc viewshed
        QVS = processing.run("grass7:r.viewshed", 
                            {'input': DEM,
                             'coordinates': "{0}, {1}".format(j, i),
                             'observer_elevation': VIEW_ELEV,
                             'max_distance': MAX_DIST,
                             'memory': MEMORY,
                             '-c': False,
                             '-r': False,
                             '-b': True,
                             '-e': True,
                             'GRASS_REGION_PARAMETER': "{0}, {1}, {2}, {3}".format(j - HALF_MAX,
                                                        j + HALF_MAX,
                                                        i - HALF_MAX,
                                                        i + HALF_MAX),
                             'GRASS_REGION_CELLSIZE_PARAMETER': 0,
                             'output': "C:/Users/Strudel/Documents/TestRoom/VS.tif"})

        # clip LC to Viewshed extent
        QLC = processing.run("gdal:cliprasterbyextent",
                            {'INPUT': LCMap,
                             'PROJWIN': "{0}, {1}, {2}, {3}".format(j - HALF_MAX,
                                         j + HALF_MAX,
                                         i - HALF_MAX,
                                         i + HALF_MAX),
                             'DATA_TYPE': 0,
                             'OUTPUT': "C:/Users/Strudel/Documents/TestRoom/LC.tif"})
        return QVS, QLC
    
    def noLag(self, ymax, ymin, xmax, xmin, HALF_MAX, res, outLib, LCnp,
              MASS_OBJECTS, DEM, VIEW_ELEV, MAX_DIST, MEMORY, LCMap,
              SIZE_ID, SHAPE_ID, HETERO_ID, COMPLEX_ID, OUTPUT):
        '''
        This is the main loop used when no lag is given.
        Every pixel will be queried.
        '''
        # numpy counters
        LCnpY = -1
        # main loop
        for i in range(ymax, ymin, -res):
            LCnpY += 1
            LCnpX = -1
            # append new row
            for name, out in outLib.items(): 
                out.append([])                
            for j in range(xmin, xmax, res):
                LCnpX += 1
                if LCnp[LCnpY,LCnpX] not in MASS_OBJECTS:
                    # calc viewshed and clip
                    QVS, QLC = self.getViewClip(i, j, DEM, VIEW_ELEV, MAX_DIST, MEMORY, HALF_MAX, LCMap)
                    
                    # convert to numpy array
                    LC = self.rst(QLC['OUTPUT'])
                    VS = self.rst(QVS['output'])                        
                    del QVS, QLC
                    
                    LC *= VS
                    # setup spatial calculator and append metrics
                    spatcalc = scapeMetrics.SpatialCalculator(VS, LC)
                    outLib['outSize'][LCnpY].append(spatcalc.calcSize(SIZE_ID))
                    outLib['outShape'][LCnpY].append(spatcalc.calcShape(SHAPE_ID))
                    outLib['outHetero'][LCnpY].append(spatcalc.calcHetero(HETERO_ID))
                    outLib['outComplex'][LCnpY].append(spatcalc.calcComplex(COMPLEX_ID))
                    del spatcalc, VS, LC
                else:
                    outLib['outSize'][LCnpY].append(-999)
                    outLib['outShape'][LCnpY].append(-999)
                    outLib['outHetero'][LCnpY].append(-999)
                    outLib['outComplex'][LCnpY].append(-999)
                    
        # export
        with open(OUTPUT[:-4] + "_Size.csv", "w+") as outfile:
            csvWriter = csv.writer(outfile, delimiter = ',')
            csvWriter.writerows(outLib['outSize'])
            
        with open(OUTPUT[:-4] + "_Shape.csv", "w+") as outfile:
            csvWriter = csv.writer(outfile, delimiter = ',')
            csvWriter.writerows(outLib['outShape'])
        
        with open(OUTPUT[:-4] + "_Hetero.csv", "w+") as outfile:
            csvWriter = csv.writer(outfile, delimiter = ',')
            csvWriter.writerows(outLib['outHetero'])
        
        with open(OUTPUT[:-4] + "_Complex.csv", "w+") as outfile:
            csvWriter = csv.writer(outfile, delimiter = ',')
            csvWriter.writerows(outLib['outComplex'])

    def withLag(self, extent, ymax, ymin, xmax, xmin, HALF_MAX, res, outLib, LCnp,
              MASS_OBJECTS, DEM, VIEW_ELEV, MAX_DIST, MEMORY, LCMap, LCMapClipObj,
              SIZE_ID, SHAPE_ID, HETERO_ID, COMPLEX_ID, OUTPUT):
        '''
        This is the main loop used when a lag is given.
        A regular grid will be made and each point location will be queried.
        '''
        # create grid
        sr = LCMap.crs().authid()
        #QMessageBox.information(None, "DEBUG:", str(int(self.globalSpinBox.text())))
        GRID = processing.run("qgis:regularpoints", 
                              {'CRS': sr,
                               'EXTENT': "{0}, {1}, {2}, {3}".format(
                                       xmin, xmax, ymin, ymax),
                               'INSET': 0,
                               'IS_SPACING': True,
                               'RANDOMIZE': False,
                               'SPACING': int(self.globalSpinBox.text()),
                               'OUTPUT': OUTPUT[:-4] + "_GRID.shp"})
        
        GRID = QgsVectorLayer(GRID['OUTPUT'])
        # make ranges
        xpt, ypt = [], []
        for pt in GRID.getFeatures():
            xpt.append(pt.geometry().asPoint().x())
            ypt.append(pt.geometry().asPoint().y())
        del GRID
        
        for i in range(len(xpt)):
#            for name, out in outLib.items(): 
#                out.append([])
            ptData = LCMapClipObj.dataProvider().identify(QgsPointXY(xpt[i], ypt[i]), QgsRaster.IdentifyFormatValue).results()[1]
            # beware: lazy evaluation! int(None) = error
            if ptData != None and int(ptData) not in MASS_OBJECTS:
                # calc viewshed and clip
                QVS, QLC = self.getViewClip(ypt[i], xpt[i], DEM, VIEW_ELEV, MAX_DIST, MEMORY, HALF_MAX, LCMap)
                
                # convert to numpy array
                LC = self.rst(QLC['OUTPUT'])
                VS = self.rst(QVS['output'])                        
                del QVS, QLC
                
                LC *= VS
                # setup spatial calculator and append metrics
                spatcalc = scapeMetrics.SpatialCalculator(VS, LC)
                outLib['outSize'].append(spatcalc.calcSize(SIZE_ID))
                outLib['outShape'].append(spatcalc.calcShape(SHAPE_ID))
                outLib['outHetero'].append(spatcalc.calcHetero(HETERO_ID))
                outLib['outComplex'].append(spatcalc.calcComplex(COMPLEX_ID))
                del spatcalc, VS, LC
            else:
                outLib['outSize'].append(-999)
                outLib['outShape'].append(-999)
                outLib['outHetero'].append(-999)
                outLib['outComplex'].append(-999)
                    
        # export
        with open(OUTPUT[:-4] + "_Size.csv", "w+") as outfile:
            csvWriter = csv.writer(outfile, delimiter = ',')
            csvWriter.writerow(outLib['outSize'])
            
        with open(OUTPUT[:-4] + "_Shape.csv", "w+") as outfile:
            csvWriter = csv.writer(outfile, delimiter = ',')
            csvWriter.writerow(outLib['outShape'])
        
        with open(OUTPUT[:-4] + "_Hetero.csv", "w+") as outfile:
            csvWriter = csv.writer(outfile, delimiter = ',')
            csvWriter.writerow(outLib['outHetero'])
        
        with open(OUTPUT[:-4] + "_Complex.csv", "w+") as outfile:
            csvWriter = csv.writer(outfile, delimiter = ',')
            csvWriter.writerow(outLib['outComplex'])
        