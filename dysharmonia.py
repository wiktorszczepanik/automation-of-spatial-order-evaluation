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


class DysharmoniaProcessingAlgorithm(QgsProcessingAlgorithm):

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return DysharmoniaProcessingAlgorithm()

    def name(self):
        return 'podciborskitabelaszesc'

    def displayName(self):
        return self.tr('dysharmonia (tabela 6)')

    def group(self):
        return self.tr('ocena ładu przestrzennego obszarów wiejskich')

    def groupId(self):
        return 'ocena ładu przestrzennego obszarów wiejskich'

    def shortHelpString(self):
        return self.tr("tabela 6")

    def initAlgorithm(self, config=None):
        
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                'INPUT3',
                self.tr('Działki ewidencyjne'),
                types=[QgsProcessing.TypeVectorPolygon]
            )
        )
        
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                'INPUT2',
                self.tr('Wody powierzchniowe'),
                types=[QgsProcessing.TypeVectorPolygon]
            )
        )
        
        self.addParameter(
            QgsProcessingParameterRasterDestination(
                'OUTPUT',
                self.tr('Output layer')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        
        
        # skrypt część I
        
        powierzchnia_dzialek = processing.run("native:fieldcalculator", {
                'INPUT': parameters['INPUT3'],
                'FIELD_NAME':'powierzchnia_dzialek',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':8,
                'FIELD_PRECISION':0,
                'FORMULA':'$area',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        difference_wd = processing.run("native:difference", 
                {'INPUT':powierzchnia_dzialek['OUTPUT'],
                'OVERLAY':parameters['INPUT2'],
                'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        powierzchnia_dzialek_min_woda = processing.run("native:fieldcalculator", {
                'INPUT': difference_wd['OUTPUT'],
                'FIELD_NAME':'powierzchnia_dzialek_min_woda',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':8,
                'FIELD_PRECISION':0,
                'FORMULA':'$area',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        udzial_powierzchniowy = processing.run("native:fieldcalculator", {
                'INPUT': powierzchnia_dzialek_min_woda['OUTPUT'],
                'FIELD_NAME':'udzial_powierzchniowy',
                'FIELD_TYPE':0,
                'FIELD_LENGTH':8,
                'FIELD_PRECISION':0,
                'FORMULA':'100-(round((("powierzchnia_dzialek_min_woda"/"powierzchnia_dzialek")*100), 3))',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        join_polygons = processing.run("native:joinattributestable", {
                'INPUT': powierzchnia_dzialek['OUTPUT'],
                'FIELD':'teryt',
                'INPUT_2': udzial_powierzchniowy['OUTPUT'],
                'FIELD_2':'teryt',
                'FIELDS_TO_COPY':['teryt', 'udzial_powierzchniowy'],
                'METHOD':1,
                'DISCARD_NONMATCHING':False,
                'PREFIX':'',
                'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
        
        ocena_dysharmonia = processing.run("native:fieldcalculator", {
                'INPUT': join_polygons['OUTPUT'],
                'FIELD_NAME':'o6',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':8,
                'FIELD_PRECISION':0,
                'FORMULA':'CASE WHEN "udzial_powierzchniowy" >= 0 AND "udzial_powierzchniowy" < 0.1 THEN 3 WHEN "udzial_powierzchniowy" >= 0.1 AND "udzial_powierzchniowy" < 1 THEN 2 WHEN "udzial_powierzchniowy" >= 1 AND "udzial_powierzchniowy" < 2.2 THEN 1 ELSE 0 END',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
        
        
        drop_fields = processing.run("native:deletecolumn", {
                'INPUT': ocena_dysharmonia['OUTPUT'],
                'COLUMN':['powierzchnia_dzialek', 'teryt_2'],
                'OUTPUT': parameters['OUTPUT']
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        
        
        
        
        return {'OUTPUT': drop_fields['OUTPUT']}
