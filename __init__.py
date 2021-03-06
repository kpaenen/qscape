# -*- coding: utf-8 -*-
"""
/***************************************************************************
 qscape
                                 A QGIS plugin
 This plugin generates a structural landscape classification map.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2018-05-24
        copyright            : (C) 2018 by Killian Paenen
        email                : kpaenen@vub.be
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""

def classFactory(iface):
    from .qscape import qscape
    return qscape(iface)
