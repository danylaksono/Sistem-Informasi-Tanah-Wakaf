# Loosely based on:
# Original C++ Tutorial 2 by Tim Sutton
# ported to Python by Martin Dobias
# with enhancements by Gary Sherman for FOSS4G2007
# Licensed under the terms of GNU GPL 2

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
import subprocess
from pyspatialite import dbapi2 as db
import sys
import os

# Import our GUI
from mainwindow_ui import Ui_MainWindow
# Import our resources (icons)
# Environment variable QGISHOME must be set to the 0.9 install directory
# before running this application
qgis_prefix = os.getenv("QGISHOME")

class MainWindow(QMainWindow, Ui_MainWindow):
	def __init__(self):	
		QMainWindow.__init__(self)
		# initialize UI
		self.setupUi(self)

		# set title
		self.setWindowTitle("Sistem Informasi Tanah Wakaf")

		# create the map canvas
		self.canvas = QgsMapCanvas()
		# set the background color
		self.canvas.setCanvasColor(QColor(255,255,255))
		self.canvas.enableAntiAliasing(True)
		self.canvas.useImageToRender(False)
		self.canvas.show()

		# layout widget
		# vertical box layout
		self.layout = QVBoxLayout(self.frame)
		self.layout.addWidget(self.canvas)

		# create dock info
		self.dockInfo = QDockWidget("Info Fitur", self)
		# self.listWidget = QListWidget()
		# self.listWidget.addItem("item1")
		# self.listWidget.addItem("item2")
		# self.listWidget.addItem("item3")
		self.label = ["Nama Pemilik", "Peruntukan", "Luas"]
		self.tabel = QTableWidget()
		self.tabel.setColumnCount(2)
		self.tabel.setRowCount(len(self.label))
		self.tabel.setHorizontalHeaderLabels(["Atribut","Value"])
		for i in range(len(self.label)):
			item = QTableWidgetItem()
			item.setText(self.label[i])
			self.tabel.setItem(i,0,item)
		self.dockInfo.setWidget(self.tabel)
		self.dockInfo.setFloating(False)
		self.dockInfo.setFeatures(QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetMovable)
		self.addDockWidget(Qt.RightDockWidgetArea, self.dockInfo)

		
		# Create Layer Set
		self.layers = []

		# Add an OGR layer to the map
		# urlWithParams = 'url=http://kaart.maaamet.ee/wms/alus&format=image/png&layers=MA-ALUS&styles=&crs=EPSG:3301'	
		# urlWithParams = 'contextualWMSLegend=0&crs=EPSG:4326&dpiMode=7&featureCount=10&format=image/gif&layers=OSM-WMS&styles=&url=http://ows.terrestris.de/osm/service?VERSION=1.1.1&'
		# rlayer = QgsRasterLayer(urlWithParams, 'OSM-WMS', 'wms')
		# QgsMapLayerRegistry.instance().addMapLayer(rlayer)
		# self.canvas.setExtent(rlayer.extent())
		# rlayer = QgsMapCanvasLayer(rlayer)
		# self.layers.append(rlayer)
		# self.canvas.setLayerSet(self.layers)

		uri = QgsDataSourceURI()
		uri.setDatabase('database.sqlite')
		uri.setDataSource('', 'db','geometry')
		vlayer = QgsVectorLayer(uri.uri(), 'lTanahWakaf', 'spatialite')
		QgsMapLayerRegistry.instance().addMapLayer(vlayer)
		self.canvas.setExtent(vlayer.extent())
		vlayer = QgsMapCanvasLayer(vlayer)
		self.layers.insert(0, vlayer)
		self.canvas.setLayerSet(self.layers)

		# Create action for tools
		self.actionAddShp = QAction(QIcon("res/AddShp.png"), "Add SHP", self.frame)
		self.actionAddCsv = QAction(QIcon("res/AddCsv.png"), "Add CSV", self.frame)
		self.actionReloadDisp = QAction(QIcon("res/reload.png"), "Reload", self.frame)
		self.actionZoomIn = QAction(QIcon("res/ZoomIn.png"), "Zoom In", self.frame)
		self.actionZoomOut = QAction(QIcon("res/ZoomOut.png"), "Zoom Out", self.frame)
		# self.actionZoomExt = QAction(QIcon("res/extent.png"), "Zoom Extent", self.frame)
		self.actionPan = QAction(QIcon("res/pan.png"), "Pan", self.frame)
		self.actionSelect = QAction(QIcon("res/select.png"), "Select", self.frame)


		# Connect action to method
		self.connect(self.actionAddShp, SIGNAL("activated()"), self.addShp)
		self.connect(self.actionAddCsv, SIGNAL("activated()"), self.addCsv)
		self.connect(self.actionReloadDisp, SIGNAL("activated()"), self.reloadDisp)
		self.connect(self.actionZoomIn, SIGNAL("activated()"), self.zoomIn)
		self.connect(self.actionZoomOut, SIGNAL("activated()"), self.zoomOut)
		# self.connect(self.actionZoomExt, SIGNAL("activated()"), self.zoomExt)
		self.connect(self.actionPan, SIGNAL("activated()"), self.pan)
		self.connect(self.actionSelect, SIGNAL("activated()"), self.select)

		# Create toolbar
		self.toolbar = self.addToolBar("Map")
		# Add actions to toolbar
		self.toolbar.addAction(self.actionAddShp)
		self.toolbar.addAction(self.actionAddCsv)
		self.toolbar.addAction(self.actionReloadDisp)
		self.toolbar.addAction(self.actionZoomIn)
		self.toolbar.addAction(self.actionZoomOut)
		# self.toolbar.addAction(self.actionZoomExt)
		self.toolbar.addAction(self.actionPan)
		self.toolbar.addAction(self.actionSelect)

		# Create map tools
		self.toolZoomIn = QgsMapToolZoom(self.canvas, False)
		self.toolZoomOut = QgsMapToolZoom(self.canvas, True)
		self.toolPan = QgsMapToolPan(self.canvas)
		self.toolSelect = QgsMapToolEmitPoint(self.canvas)

	# Set map tool to select feature
	def select(self):
		self.canvas.setMapTool(self.toolSelect)
		self.connect(self.toolSelect, SIGNAL("canvasClicked(const QgsPoint &,Qt::MouseButton)"), self.selectFeature)

	def selectFeature(self, point):
		active = QgsMapLayerRegistry.instance().mapLayersByName("lTanahWakaf")[0]
		active.removeSelection()

		searchRadius = self.canvas.mapUnitsPerPixel() * 5
		rect = QgsRectangle()
		rect.setXMinimum( point.x() - searchRadius )
		rect.setXMaximum( point.x() + searchRadius )
		rect.setYMinimum( point.y() - searchRadius )
		rect.setYMaximum( point.y() + searchRadius )
		
		active.select(rect, False)
		selected = active.selectedFeatures()
		for feature in selected:
			# feature.setSelectionColor( QColor("red") )
			print feature.id()
			self.showDock()

	# Set map tool to Zoom In
	def zoomIn(self):
		self.canvas.setMapTool(self.toolZoomIn)

	# Set map tool to Zoom Out
	def zoomOut(self):
		self.canvas.setMapTool(self.toolZoomOut)

	# Set map tool to Zoom Out
	def addCsv(self):
		self.canvas.setMapTool(self.toolZoomOut)
	
	# Set map tool to Zoom Extent
	# def zoomExt(self ):
	# 	self.canvas.fullExtent()
	
	# Set map tool to Pan
	def pan(self):
		self.canvas.setMapTool(self.toolPan)

	# Set map tool to Refresh
	def reloadDisp(self):
	    self.canvas.refresh()

	# Set map tool to add shapefile
	def addShp(self):
		file = QFileDialog.getOpenFileName(self, "Open Shapefile", ".", "Shapefiles (*.shp)")
		fileInfo = QFileInfo(file)
		
		# Add layer
		layer = QgsVectorLayer(file, fileInfo.fileName(), "ogr")
		# subprocess.call(["spatialite_tool", "-i", "-shp", str(file).strip('.shp'), "-d", "db.sqlite", "-t", 'db', "-g", "GEOMETRY", "-c", "UTF-8","-s","3042", "--type", "MULTIPOLYGON"])

		# creating/connecting the test_db
		conn = db.connect('database.sqlite')

		# creating a Cursor
		cur = conn.cursor()
		sql = 'CREATE VIRTUAL TABLE ne50pp USING VirtualShape("'+str(file).strip('.shp')+'", "CP1251", 4326)'
		cur.execute(sql)

		sql = 'INSERT INTO db (name, geometry) SELECT date("now") as name, Geometry as Geometry FROM ne50pp'
		cur.execute(sql)		
		
		sql = 'DROP TABLE ne50pp'
		cur.execute(sql)

		if not layer.isValid():
			return

		# Add layer to registry
		QgsMapLayerRegistry.instance().addMapLayer(layer)

		# Set extent to the layer
		self.canvas.setExtent(layer.extent())

		# Set up the map canvas layer set
		cl = QgsMapCanvasLayer(layer)
		self.layers.insert(0, cl)
		self.canvas.setLayerSet(self.layers)

def main(argv):
	# create Qt application
	app = QApplication(argv)
	# Initialize qgis libraries
	QgsApplication.setPrefixPath(qgis_prefix, True)
	QgsApplication.initQgis()
	# create main window
	wnd = MainWindow()
	# Move the app window to upper left
	wnd.move(100,100)
	wnd.show()
	# run!
	retval = app.exec_()
	# exit
	QgsApplication.exitQgis()
	sys.exit(retval)

if __name__ == "__main__":
	main(sys.argv)