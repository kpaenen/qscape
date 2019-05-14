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

from builtins import object
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction
from qgis.core import QgsProject, QgsRasterLayer
from qgis.analysis import QgsRasterCalculatorEntry, QgsRasterCalculator

from . import resources
from . import doQscape
import os
import processing

class qscape(object):

    def __init__(self, iface):
        self.iface = iface

    def initGui(self):
        # create action
        self.action = QAction(QIcon(":/plugins/qscape/icon.png"), "QScape", self.iface.mainWindow())
        self.action.setWhatsThis("Calculates structural landscape parameters")
        self.action.triggered.connect(self.run)
        # add toolbar button and menu item
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("&Analyses", self.action)

    def unload(self):
        # remove plugin menu item and icon
        self.iface.removePluginMenu("&Analyses", self.action)
        self.iface.removeToolBarIcon(self.action)

    def run(self):
        # create and show configuration dialog
        dlg = doQscape.Dialog(self.iface)
        result = dlg.exec_()
        
        # see if OK pressed
        if result == 1:
            # load input
            LCMap = QgsProject.instance().mapLayersByName(str(dlg.inRastCombo.currentText()))[0]
            DEM = QgsProject.instance().mapLayersByName(str(dlg.inDEMCombo.currentText()))[0]
            
            # assign variables
            massTemp = dlg.massLineEdit.text()
            MASS_OBJECTS = [None if massTemp == '' else int(i) for i in massTemp.split(',')]
            MASS_OBJECTS = [0] + MASS_OBJECTS # mask out background
            del massTemp
            VIEW_ELEV = float(dlg.heightDSpinBox.text().replace(',','.'))
            MAX_DIST = float(dlg.radiusDSpinBox.text().replace(',','.'))
            HALF_MAX = int(MAX_DIST / 2)
            MEMORY = int(dlg.memorySpinBox.text())
            OUTPUT = dlg.outLineEdit.text()
            OUTDIR = OUTPUT.rsplit("/", 1)[0]
            
            ## make initial clip
            # make global mask
            OUTMASK = OUTDIR + "/LC_Mask.tif"
            LCEntry = QgsRasterCalculatorEntry()
            LCEntry.ref = 'mask@1'
            LCEntry.raster = LCMap
            LCEntry.bandNumber = 1
            entry = [LCEntry]
            
            LCCalc = QgsRasterCalculator('mask@1 > 0',
                                         OUTMASK, 
                                         'GTiff',
                                         LCMap.extent(), LCMap.width(), LCMap.height(),
                                         entry)
            LCCalc.processCalculation()
            del LCEntry, LCCalc, entry
            #LCMask = QgsProject.instance().mapLayersByName(OUTMASK)
            
            # raster vector
            LCVect = processing.run("gdal:polygonize",
                                    {'INPUT': OUTMASK,
                                     'BAND': 1,
                                     'FIELD': 'DN',
                                     'EIGHT_CONNECTEDNESS': False,
                                     'OUTPUT': OUTDIR + "/LC_Vect.shp"})
            
            LCBuff = processing.run("native:buffer", 
                                    {'INPUT': LCVect['OUTPUT'],
                                     'DISTANCE': -MAX_DIST, #-(halfmax + lag/2)?
                                     'SEGMENTS': 5,
                                     'END_CAP_STYLE': 0,
                                     'JOIN_STYLE': 2,
                                     'MITER_LIMIT': 2,
                                     'DISSOLVE': True,
                                     'OUTPUT': OUTDIR + "/LC_Buff.shp"})
            
            LCMapClip = processing.run("gdal:cliprasterbymasklayer", 
                                       {'INPUT': LCMap,
                                        'MASK': LCBuff['OUTPUT'],
                                        'NODATA': 0,
                                        'ALPHA_BAND': False,
                                        'CROP_TO_CUTLINE': True,
                                        'KEEP_RESOLUTION': True,
                                        'DATA_TYPE': 0,
                                        'OUTPUT': OUTDIR + "/LC_Clip.tif"})
            # cleanup        
            del OUTMASK, LCVect, LCBuff
            [os.remove(os.path.join(OUTDIR, f)) for f in os.listdir(OUTDIR) if (f.startswith("LC_Vect")
                                                                                or f.startswith("LC_Buff")
                                                                                or f.startswith("LC_Mask"))]

            
            # define extent and resolution
            LCMapClipObj = QgsRasterLayer(LCMapClip['OUTPUT'])
            extent = LCMapClipObj.extent()
            xmin = int(extent.xMinimum())
            xmax = int(extent.xMaximum())
            ymin = int(extent.yMinimum())
            ymax = int(extent.yMaximum())
            res = int(LCMap.rasterUnitsPerPixelX())

            # convert clip to numpy
            LCnp = dlg.rst(LCMapClip['OUTPUT'])
        
            # initialise output metrics
            outLib = {'outSize': [],
                      'outShape': [],
                      'outHetero': [],
                      'outComplex': []}
            
            # check which measures
            SIZE_ID, SHAPE_ID, HETERO_ID, COMPLEX_ID = dlg.checkMeasures()         
            
            # main loop
            # check if lag
            if int(dlg.globalSpinBox.text()) == 0:
                dlg.noLag(ymax, ymin, xmax, xmin, HALF_MAX, res, outLib, LCnp,
                          MASS_OBJECTS, DEM, VIEW_ELEV, MAX_DIST, MEMORY, LCMap,
                          SIZE_ID, SHAPE_ID, HETERO_ID, COMPLEX_ID, OUTPUT, OUTDIR)
            else:
                dlg.withLag(extent, ymax, ymin, xmax, xmin, HALF_MAX, res, outLib, LCnp,
                  MASS_OBJECTS, DEM, VIEW_ELEV, MAX_DIST, MEMORY, LCMap, LCMapClipObj,
                  SIZE_ID, SHAPE_ID, HETERO_ID, COMPLEX_ID, OUTPUT, OUTDIR)
            
            # last cleanup
            '''
            [os.remove(os.path.join(OUTDIR, f)) for f in os.listdir(OUTDIR) if (f.startswith("LC.")
                                                                                or f.startswith("VS."))]
            '''
            
            '''
            # numpy counters
            LCnpY = -1
            # main loop
            for i in range(ymax - HALF_MAX, ymin + HALF_MAX, -res):
                LCnpY += 1
                LCnpX = -1
                # append new row
                for name, out in outLib.items(): 
                    out.append([])                
                for j in range(xmin + HALF_MAX, xmax - HALF_MAX, res):
                    LCnpX += 1
                    if LCnp[LCnpY,LCnpX] not in MASS_OBJECTS:
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
                        
                        # convert to numpy array
                        LC = dlg.rst(QLC['OUTPUT'])
                        VS = dlg.rst(QVS['output'])                        
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
            '''