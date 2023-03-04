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
        
        
        #skrypt część I
        
        powierzchnia_dzialki = processing.run("native:fieldcalculator", {
                'INPUT': parameters['INPUT'],
                'FIELD_NAME':'powierzchnia_dzialki',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':10,
                'FIELD_PRECISION':0,
                'FORMULA':'$area',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        dissolve_uzytki = processing.run("native:dissolve", {
                'INPUT':parameters['INPUT2'],
                'FIELD':['uzytki_gru'],
                'SEPARATE_DISJOINT':True,
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)

        intersection_by_pol = processing.run("native:intersection", {
                'INPUT':powierzchnia_dzialki['OUTPUT'],
                'OVERLAY':dissolve_uzytki['OUTPUT'],
                'INPUT_FIELDS':[],
                'OVERLAY_FIELDS':[],
                'OVERLAY_FIELDS_PREFIX':'',
                'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        powierzchnia_uzytku = processing.run("native:fieldcalculator", {
                'INPUT': intersection_by_pol['OUTPUT'],
                'FIELD_NAME':'powierzchnia_uzytku',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':8,
                'FIELD_PRECISION':0,
                'FORMULA':'$area',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        centroid_uz = processing.run("native:centroids", {
                'INPUT':powierzchnia_uzytku['OUTPUT'],
                'ALL_PARTS':False,
                'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        warunek_powierzchniowy = processing.run("native:fieldcalculator", {
                'INPUT': centroid_uz['OUTPUT'],
                'FIELD_NAME':'warunek_powierzchniowy',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':5,
                'FIELD_PRECISION':0,
                'FORMULA':'if(round((("powierzchnia_uzytku"/"powierzchnia_dzialki")*100), 0) > 1, 1, 0)',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        delete_attr = processing.run("native:extractbyattribute", {
                'INPUT':warunek_powierzchniowy['OUTPUT'],
                'FIELD':'warunek_powierzchniowy',
                'OPERATOR':0,
                'VALUE':'1',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        spatial_index = processing.run("native:createspatialindex", {
                'INPUT': delete_attr['OUTPUT']}, is_child_algorithm=True, context=context, feedback=feedback)
                
        pukty_w_poligonie = processing.run("native:countpointsinpolygon", {
                'POLYGONS':powierzchnia_dzialki['OUTPUT'],
                'POINTS':delete_attr['OUTPUT'],
                'WEIGHT':'',
                'CLASSFIELD':'',
                'FIELD':'pukty_w_poligonie',
                'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        ocena_jednorodnosc = processing.run("native:fieldcalculator", {
                'INPUT': pukty_w_poligonie['OUTPUT'],
                'FIELD_NAME':'ocena_jednorodnosc',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':8,
                'FIELD_PRECISION':0,
                'FORMULA':'CASE\r\nWHEN "pukty_w_poligonie" = 1 AND ("powierzchnia_dzialki" >= 0 AND "powierzchnia_dzialki" <= 70000) THEN 5\r\nWHEN "pukty_w_poligonie" = 2 AND ("powierzchnia_dzialki" > 2000 AND "powierzchnia_dzialki" <= 5000) THEN 1\r\nWHEN "pukty_w_poligonie" = 2 AND ("powierzchnia_dzialki" > 5000 AND "powierzchnia_dzialki" <= 10000) THEN 2\r\nWHEN "pukty_w_poligonie" = 2 AND ("powierzchnia_dzialki" > 10000 AND "powierzchnia_dzialki" <= 20000) THEN 3\r\nWHEN "pukty_w_poligonie" = 2 AND ("powierzchnia_dzialki" > 20000 AND "powierzchnia_dzialki" <= 40000) THEN 4\r\nWHEN "pukty_w_poligonie" = 2 AND ("powierzchnia_dzialki" > 40000 AND "powierzchnia_dzialki" <= 70000) THEN 5\r\nWHEN "pukty_w_poligonie" = 3 AND ("powierzchnia_dzialki" > 5000 AND "powierzchnia_dzialki" <= 10000) THEN 1\r\nWHEN "pukty_w_poligonie" = 3 AND ("powierzchnia_dzialki" > 10000 AND "powierzchnia_dzialki" <= 15000) THEN 2\r\nWHEN "pukty_w_poligonie" = 3 AND ("powierzchnia_dzialki" > 15000 AND "powierzchnia_dzialki" <= 30000) THEN 3\r\nWHEN "pukty_w_poligonie" = 3 AND ("powierzchnia_dzialki" > 30000 AND "powierzchnia_dzialki" <= 60000) THEN 4\r\nWHEN "pukty_w_poligonie" = 3 AND ("powierzchnia_dzialki" > 60000 AND "powierzchnia_dzialki" <= 70000) THEN 5\r\nWHEN "pukty_w_poligonie" = 4 AND ("powierzchnia_dzialki" > 5000 AND "powierzchnia_dzialki" <= 10000) THEN 1\r\nWHEN "pukty_w_poligonie" = 4 AND ("powierzchnia_dzialki" > 10000 AND "powierzchnia_dzialki" <= 20000) THEN 2\r\nWHEN "pukty_w_poligonie" = 4 AND ("powierzchnia_dzialki" > 20000 AND "powierzchnia_dzialki" <= 40000) THEN 3\r\nWHEN "pukty_w_poligonie" = 4 AND ("powierzchnia_dzialki" > 40000 AND "powierzchnia_dzialki" <= 70000) THEN 4\r\nWHEN "pukty_w_poligonie" = 5 AND ("powierzchnia_dzialki" > 5000 AND "powierzchnia_dzialki" <= 15000) THEN 1\r\nWHEN "pukty_w_poligonie" = 5 AND ("powierzchnia_dzialki" > 15000 AND "powierzchnia_dzialki" <= 25000) THEN 2\r\nWHEN "pukty_w_poligonie" = 5 AND ("powierzchnia_dzialki" > 25000 AND "powierzchnia_dzialki" <= 50000) THEN 3\r\nWHEN "pukty_w_poligonie" = 5 AND ("powierzchnia_dzialki" > 50000 AND "powierzchnia_dzialki" <= 70000) THEN 4\r\nWHEN "pukty_w_poligonie" = 6 AND ("powierzchnia_dzialki" > 5000 AND "powierzchnia_dzialki" <= 10000) THEN 1\r\nWHEN "pukty_w_poligonie" = 6 AND ("powierzchnia_dzialki" > 10000 AND "powierzchnia_dzialki" <= 30000) THEN 2\r\nWHEN "pukty_w_poligonie" = 6 AND ("powierzchnia_dzialki" > 30000 AND "powierzchnia_dzialki" <= 60000) THEN 3\r\nWHEN "pukty_w_poligonie" = 6 AND ("powierzchnia_dzialki" > 60000 AND "powierzchnia_dzialki" <= 70000) THEN 4\r\nWHEN "pukty_w_poligonie" = 7 AND ("powierzchnia_dzialki" > 5000 AND "powierzchnia_dzialki" <= 20000) THEN 1\r\nWHEN "pukty_w_poligonie" = 7 AND ("powierzchnia_dzialki" > 20000 AND "powierzchnia_dzialki" <= 35000) THEN 2\r\nWHEN "pukty_w_poligonie" = 7 AND ("powierzchnia_dzialki" > 35000 AND "powierzchnia_dzialki" <= 70000) THEN 3\r\nWHEN "pukty_w_poligonie" = 8 AND ("powierzchnia_dzialki" > 10000 AND "powierzchnia_dzialki" <= 25000) THEN 1\r\nWHEN "pukty_w_poligonie" = 8 AND ("powierzchnia_dzialki" > 25000 AND "powierzchnia_dzialki" <= 40000) THEN 2\r\nWHEN "pukty_w_poligonie" = 8 AND ("powierzchnia_dzialki" > 40000 AND "powierzchnia_dzialki" <= 70000) THEN 3\r\nWHEN "pukty_w_poligonie" = 9 AND ("powierzchnia_dzialki" > 10000 AND "powierzchnia_dzialki" <= 30000) THEN 1\r\nWHEN "pukty_w_poligonie" = 9 AND ("powierzchnia_dzialki" > 30000 AND "powierzchnia_dzialki" <= 45000) THEN 2\r\nWHEN "pukty_w_poligonie" = 9 AND ("powierzchnia_dzialki" > 45000 AND "powierzchnia_dzialki" <= 70000) THEN 3\r\nWHEN "pukty_w_poligonie" = 10 AND ("powierzchnia_dzialki" > 10000 AND "powierzchnia_dzialki" <= 35000) THEN 1\r\nWHEN "pukty_w_poligonie" = 10 AND ("powierzchnia_dzialki" > 35000 AND "powierzchnia_dzialki" <= 50000) THEN 2\r\nWHEN "pukty_w_poligonie" = 10 AND ("powierzchnia_dzialki" > 50000 AND "powierzchnia_dzialki" <= 70000) THEN 3\r\nWHEN "pukty_w_poligonie" = 11 AND ("powierzchnia_dzialki" > 10000 AND "powierzchnia_dzialki" <= 35000) THEN 1\r\nWHEN "pukty_w_poligonie" = 11 AND ("powierzchnia_dzialki" > 35000 AND "powierzchnia_dzialki" <= 55000) THEN 2\r\nWHEN "pukty_w_poligonie" = 11 AND ("powierzchnia_dzialki" > 55000 AND "powierzchnia_dzialki" <= 70000) THEN 3\r\nWHEN "pukty_w_poligonie" = 12 AND ("powierzchnia_dzialki" > 10000 AND "powierzchnia_dzialki" <= 40000) THEN 1\r\nWHEN "pukty_w_poligonie" = 12 AND ("powierzchnia_dzialki" > 40000 AND "powierzchnia_dzialki" <= 60000) THEN 2\r\nWHEN "pukty_w_poligonie" = 12 AND ("powierzchnia_dzialki" > 60000 AND "powierzchnia_dzialki" <= 70000) THEN 3\r\nELSE 0\r\nEND',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        
        drop_fields = processing.run("native:deletecolumn", {
                'INPUT': ocena_jednorodnosc['OUTPUT'],
                'COLUMN':[''],
                'OUTPUT': parameters['OUTPUT']
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        return {'OUTPUT': drop_fields['OUTPUT']}
