@echo off
call "C:\OSGeo4W64\bin\o4w_env.bat"
call "C:\OSGeo4W64\bin\qt5_env.bat"
call "C:\OSGeo4W64\bin\py3_env.bat"

@echo on
pyrcc5 -o C:\Users\Strudel\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\qscape\resources.py C:\Users\Strudel\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\qscape\resources.qrc