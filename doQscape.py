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
from PyQt5 import uic
from PyQt5.QtCore import Qt, QFile, QFileInfo, QVariant
from PyQt5.QtWidgets import QDialog, QFileDialog, QInputDialog, QMessageBox, QTableWidgetItem
from qgis.core import (
    QgsFields,
    QgsField,
    QgsFeature,
    QgsGeometry,
    QgsFeatureRequest,
    QgsProject,
    QgsRaster,
    QgsRectangle,
    QgsVectorFileWriter,
    QgsVectorLayer,
    QgsWkbTypes
)

Ui_Dialog = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'qscapeUi.ui'))[0]

class Dialog(QDialog, Ui_Dialog):
    
    LCMap = {}
    DEM = {}
    massObjects = []
    viewElev = 0
    radius = -1
    coverage = 100
    memory = 500
    output = {}
    
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
        
