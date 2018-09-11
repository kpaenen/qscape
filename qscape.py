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
from qgis.core import (
        QgsProject
)

from . import resources
from . import doQscape

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
        dlg.exec_()
        
        # see if OK pressed
        if dlg:
            # load input
            LCMap = QgsProject.instance().mapLayersByName(str(dlg.inRastCombo.currentText()))
            DEM = QgsProject.instance().mapLayersByName(str(dlg.inDEMCombo.currentText()))
            
