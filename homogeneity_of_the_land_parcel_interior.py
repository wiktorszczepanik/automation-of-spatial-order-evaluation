# -*- coding: utf-8 -*-

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterRasterDestination,
                       QgsCoordinateReferenceSystem,
                       QgsProperty)
from qgis import processing


class JednorodnoscProcessingAlgorithm(QgsProcessingAlgorithm):

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return JednorodnoscProcessingAlgorithm()

    def name(self):
        return 'podciborskitabeladziewiec'

    def displayName(self):
        return self.tr('ocena jednorodności wnętrza działki (tabela 9)')

    def group(self):
        return self.tr('ocena ładu przestrzennego obszarów wiejskich')

    def groupId(self):
        return 'ocena ładu przestrzennego obszarów wiejskich'

    def shortHelpString(self):
        return self.tr("tabela 9")

    def initAlgorithm(self, config=None):
        
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                'INPUT',
                self.tr('Działki ewidencyjne'),
                types=[QgsProcessing.TypeVectorPolygon]
            )
        )
        
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                'INPUT2',
                self.tr('Użytki gruntowe'),
                types=[QgsProcessing.TypeVectorPolygon]
            )
        )
        
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                'OUTPUT',
                self.tr('Output layer')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        
        
        # script I part
        
        area_plot = processing.run("native:fieldcalculator", {
                'INPUT': parameters['INPUT'],
                'FIELD_NAME':'area_plot',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':10,
                'FIELD_PRECISION':0,
                'FORMULA':'$area',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        dissolve_land_use = processing.run("native:dissolve", {
                'INPUT':parameters['INPUT2'],
                'FIELD':['uzytki_gru'],
                'SEPARATE_DISJOINT':True,
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)

        intersection_by_polygon = processing.run("native:intersection", {
                'INPUT':area_plot['OUTPUT'],
                'OVERLAY':dissolve_land_use['OUTPUT'],
                'INPUT_FIELDS':[],
                'OVERLAY_FIELDS':[],
                'OVERLAY_FIELDS_PREFIX':'',
                'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        area_land_use = processing.run("native:fieldcalculator", {
                'INPUT': intersection_by_polygon['OUTPUT'],
                'FIELD_NAME':'area_land_use',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':8,
                'FIELD_PRECISION':0,
                'FORMULA':'$area',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        centroid_land_use = processing.run("native:centroids", {
                'INPUT':area_land_use['OUTPUT'],
                'ALL_PARTS':False,
                'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        case_area_lu_plot = processing.run("native:fieldcalculator", {
                'INPUT': centroid_land_use['OUTPUT'],
                'FIELD_NAME':'case_area_lu_plot',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':5,
                'FIELD_PRECISION':0,
                'FORMULA':'if(round((("area_land_use"/"area_plot")*100), 0) > 1, 1, 0)',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        delete_attr = processing.run("native:extractbyattribute", {
                'INPUT':case_area_lu_plot['OUTPUT'],
                'FIELD':'case_area_lu_plot',
                'OPERATOR':0,
                'VALUE':'1',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        spatial_index = processing.run("native:createspatialindex", {
                'INPUT': delete_attr['OUTPUT']}, is_child_algorithm=True, context=context, feedback=feedback)
                
        points_polygon = processing.run("native:countpointsinpolygon", {
                'POLYGONS':area_plot['OUTPUT'],
                'POINTS':delete_attr['OUTPUT'],
                'WEIGHT':'',
                'CLASSFIELD':'',
                'FIELD':'points_polygon',
                'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        case_evaluation = processing.run("native:fieldcalculator", {
                'INPUT': points_polygon['OUTPUT'],
                'FIELD_NAME':'case_evaluation',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':8,
                'FIELD_PRECISION':0,
                'FORMULA':'CASE\r\nWHEN "points_polygon" = 1 AND ("area_plot" >= 0 AND "area_plot" <= 70000) THEN 5\r\nWHEN "points_polygon" = 2 AND ("area_plot" > 2000 AND "area_plot" <= 5000) THEN 1\r\nWHEN "points_polygon" = 2 AND ("area_plot" > 5000 AND "area_plot" <= 10000) THEN 2\r\nWHEN "points_polygon" = 2 AND ("area_plot" > 10000 AND "area_plot" <= 20000) THEN 3\r\nWHEN "points_polygon" = 2 AND ("area_plot" > 20000 AND "area_plot" <= 40000) THEN 4\r\nWHEN "points_polygon" = 2 AND ("area_plot" > 40000 AND "area_plot" <= 70000) THEN 5\r\nWHEN "points_polygon" = 3 AND ("area_plot" > 5000 AND "area_plot" <= 10000) THEN 1\r\nWHEN "points_polygon" = 3 AND ("area_plot" > 10000 AND "area_plot" <= 15000) THEN 2\r\nWHEN "points_polygon" = 3 AND ("area_plot" > 15000 AND "area_plot" <= 30000) THEN 3\r\nWHEN "points_polygon" = 3 AND ("area_plot" > 30000 AND "area_plot" <= 60000) THEN 4\r\nWHEN "points_polygon" = 3 AND ("area_plot" > 60000 AND "area_plot" <= 70000) THEN 5\r\nWHEN "points_polygon" = 4 AND ("area_plot" > 5000 AND "area_plot" <= 10000) THEN 1\r\nWHEN "points_polygon" = 4 AND ("area_plot" > 10000 AND "area_plot" <= 20000) THEN 2\r\nWHEN "points_polygon" = 4 AND ("area_plot" > 20000 AND "area_plot" <= 40000) THEN 3\r\nWHEN "points_polygon" = 4 AND ("area_plot" > 40000 AND "area_plot" <= 70000) THEN 4\r\nWHEN "points_polygon" = 5 AND ("area_plot" > 5000 AND "area_plot" <= 15000) THEN 1\r\nWHEN "points_polygon" = 5 AND ("area_plot" > 15000 AND "area_plot" <= 25000) THEN 2\r\nWHEN "points_polygon" = 5 AND ("area_plot" > 25000 AND "area_plot" <= 50000) THEN 3\r\nWHEN "points_polygon" = 5 AND ("area_plot" > 50000 AND "area_plot" <= 70000) THEN 4\r\nWHEN "points_polygon" = 6 AND ("area_plot" > 5000 AND "area_plot" <= 10000) THEN 1\r\nWHEN "points_polygon" = 6 AND ("area_plot" > 10000 AND "area_plot" <= 30000) THEN 2\r\nWHEN "points_polygon" = 6 AND ("area_plot" > 30000 AND "area_plot" <= 60000) THEN 3\r\nWHEN "points_polygon" = 6 AND ("area_plot" > 60000 AND "area_plot" <= 70000) THEN 4\r\nWHEN "points_polygon" = 7 AND ("area_plot" > 5000 AND "area_plot" <= 20000) THEN 1\r\nWHEN "points_polygon" = 7 AND ("area_plot" > 20000 AND "area_plot" <= 35000) THEN 2\r\nWHEN "points_polygon" = 7 AND ("area_plot" > 35000 AND "area_plot" <= 70000) THEN 3\r\nWHEN "points_polygon" = 8 AND ("area_plot" > 10000 AND "area_plot" <= 25000) THEN 1\r\nWHEN "points_polygon" = 8 AND ("area_plot" > 25000 AND "area_plot" <= 40000) THEN 2\r\nWHEN "points_polygon" = 8 AND ("area_plot" > 40000 AND "area_plot" <= 70000) THEN 3\r\nWHEN "points_polygon" = 9 AND ("area_plot" > 10000 AND "area_plot" <= 30000) THEN 1\r\nWHEN "points_polygon" = 9 AND ("area_plot" > 30000 AND "area_plot" <= 45000) THEN 2\r\nWHEN "points_polygon" = 9 AND ("area_plot" > 45000 AND "area_plot" <= 70000) THEN 3\r\nWHEN "points_polygon" = 10 AND ("area_plot" > 10000 AND "area_plot" <= 35000) THEN 1\r\nWHEN "points_polygon" = 10 AND ("area_plot" > 35000 AND "area_plot" <= 50000) THEN 2\r\nWHEN "points_polygon" = 10 AND ("area_plot" > 50000 AND "area_plot" <= 70000) THEN 3\r\nWHEN "points_polygon" = 11 AND ("area_plot" > 10000 AND "area_plot" <= 35000) THEN 1\r\nWHEN "points_polygon" = 11 AND ("area_plot" > 35000 AND "area_plot" <= 55000) THEN 2\r\nWHEN "points_polygon" = 11 AND ("area_plot" > 55000 AND "area_plot" <= 70000) THEN 3\r\nWHEN "points_polygon" = 12 AND ("area_plot" > 10000 AND "area_plot" <= 40000) THEN 1\r\nWHEN "points_polygon" = 12 AND ("area_plot" > 40000 AND "area_plot" <= 60000) THEN 2\r\nWHEN "points_polygon" = 12 AND ("area_plot" > 60000 AND "area_plot" <= 70000) THEN 3\r\nELSE 0\r\nEND',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        # cleanig data
        
        drop_fields = processing.run("native:deletecolumn", {
                'INPUT': case_evaluation['OUTPUT'],
                'COLUMN':[''],
                'OUTPUT': parameters['OUTPUT']
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        return {'OUTPUT': drop_fields['OUTPUT']}
