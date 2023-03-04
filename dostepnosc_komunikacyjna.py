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


class DostepnoscKomunikacyjnaProcessingAlgorithm(QgsProcessingAlgorithm):

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return DostepnoscKomunikacyjnaProcessingAlgorithm()

    def name(self):
        return 'podciborskitabelapiec'

    def displayName(self):
        return self.tr('dostępność komunikacjna (tabela 5)')

    def group(self):
        return self.tr('ocena ładu przestrzennego obszarów wiejskich')

    def groupId(self):
        return 'ocena ładu przestrzennego obszarów wiejskich'

    def shortHelpString(self):
        return self.tr("tabela 5")

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
                self.tr('Drogi'),
                types=[QgsProcessing.TypeVectorLine]
            )
        )
        
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                'OUTPUT',
                self.tr('Output layer')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        
        
        # skrypt część I
         
        obreby = processing.run("native:fieldcalculator", {
                'INPUT':parameters['INPUT'],
                'FIELD_NAME':'obreby',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':8,
                'FIELD_PRECISION':0,
                'FORMULA':'substr("teryt", 12, 2)',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
        
        dissolve_obr = processing.run("native:dissolve", {
                'INPUT':obreby['OUTPUT'],
                'FIELD':['obreby'],
                'SEPARATE_DISJOINT':True,
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
        
        powierzchnia = processing.run("native:fieldcalculator", {
                'INPUT':dissolve_obr['OUTPUT'],
                'FIELD_NAME':'powierzchnia',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':8,
                'FIELD_PRECISION':0,
                'FORMULA':'round($area, 0)',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
        
        sumline_poligon = processing.run("native:sumlinelengths", {
                'POLYGONS':powierzchnia['OUTPUT'],
                'LINES':parameters['INPUT2'],
                'LEN_FIELD':'dlugosc_drog',
                'COUNT_FIELD':'count',
                'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        stopien_nasycenia = processing.run("native:fieldcalculator", {
                'INPUT': sumline_poligon['OUTPUT'],
                'FIELD_NAME':'stopien_nasycenia',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':8,
                'FIELD_PRECISION':0,
                'FORMULA':'("dlugosc_drog"*10000)/"powierzchnia"',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        ocena_nasycenia = processing.run("native:fieldcalculator", {
                'INPUT': stopien_nasycenia['OUTPUT'],
                'FIELD_NAME':'o5',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':8,
                'FIELD_PRECISION':0,
                'FORMULA':'CASE WHEN "stopien_nasycenia" >= 0 AND "stopien_nasycenia" < 10 THEN 0 WHEN "stopien_nasycenia" >= 10 AND "stopien_nasycenia" < 20 THEN 1 WHEN "stopien_nasycenia" >= 20 AND "stopien_nasycenia" < 30 THEN 2 WHEN "stopien_nasycenia" >= 30 AND "stopien_nasycenia" < 40 THEN 3 WHEN "stopien_nasycenia" >= 40 AND "stopien_nasycenia" < 50 THEN 2 WHEN "stopien_nasycenia" >= 50 AND "stopien_nasycenia" < 60 THEN 1 WHEN "stopien_nasycenia" >= 60 THEN 0 ELSE 0 END',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        join_dla_dzialek = processing.run("native:joinattributestable", {
                'INPUT': obreby['OUTPUT'],
                'FIELD':'obreby',
                'INPUT_2': ocena_nasycenia['OUTPUT'],
                'FIELD_2':'obreby',
                'FIELDS_TO_COPY':['o5'],
                'METHOD':1,
                'DISCARD_NONMATCHING':False,
                'PREFIX':'',
                'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        
        drop_fields = processing.run("native:deletecolumn", {
                'INPUT': join_dla_dzialek['OUTPUT'],
                'COLUMN':[''],
                'OUTPUT': parameters['OUTPUT']
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        
        
        
        
        return {'OUTPUT': drop_fields['OUTPUT']}
