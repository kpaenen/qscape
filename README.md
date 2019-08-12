# qscape
A QGIS plugin for generating structural landscape classification maps.

# prerequisites
- QGIS 3.x
- Python 3.6
  - numpy
  - numpy_indexed (will be automatically installed on startup if not present)
  - osgeo including GDAL
  
The safest choice is to: 
- install Python 3 via Anaconda, this ensures all needed packages.
- install QGIS 3 via the OSGeo4W installer (make sure to also install GRASS) from: 
    https://qgis.org/en/site/forusers/download.html

# installation
Copy forked repository in:
  > C:\Users\<User>\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\qscape

# enabling QScape
- Start up 'QGIS Desktop with GRASS'.
- In the toolbar choose 'Plugins>Install plugins', find QScape and enable it. It should now appear in the toolbar.

# starting QScape
- Insert a land cover map. Ensure a good definition of the land cover classes.
    Note: you will lose a border with a width equal to the maximum visibility radius because of the moving window technique used.
- Indicate which land cover classes should be masked out.
- Insert a height model of the same area (i.e. DEM, DSM,...).
    Note: This model is allowed to be larger than the land cover map. Coordinates based on the land cover map are used in the modelling.
- Choose the viewing elevation above the ground i.e. the eye height.
- Choose the maximum visibility radius i.e. the limit of how far the observer can see.
- Choose a lag distance i.e. how many pixels will be skipped, everything above 0 will generate a regular grid.
- Choose desired spatial metrics. One per aspect.
- Choose the amount of RAM to allocate to the viewshed processing.
- Choose the output location and name.

  Note: This can take a long time for large study areas and low lag distances. 
  QGIS may seem to freeze, but the tool will still continue running in the background.
  
# known bugs and problems
- Script may fail with "invalid object" error.
  This can be solved by going to 'Toolbox>Options>Processing>General>Filter invalid objects' and choose 'Do not filter'
- Accessing feature layer attributes in QGIS at the time of writing knows a memory leak. 
  This may cause premature failure if the modelling takes longer than a day.
- NoData pixels within the land cover map will also be subjected to buffering and may lead to large holes in the output data.
- QGIS may freeze after the completion of the modelling. Freezes during the analysis will not stop the script.

# features to be added in future releases
- Single point processing
- Resolve performance issues further
- Add progress bar
- Further improve documentation
