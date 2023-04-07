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
        
        
        # script I part
         
        districts = processing.run("native:fieldcalculator", {
                'INPUT':parameters['INPUT'],
                'FIELD_NAME':'districts',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':8,
                'FIELD_PRECISION':0,
                'FORMULA':'substr("teryt", 12, 2)',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
        
        dissolve_districts = processing.run("native:dissolve", {
                'INPUT':districts['OUTPUT'],
                'FIELD':['districts'],
                'SEPARATE_DISJOINT':True,
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
        
        area_districts = processing.run("native:fieldcalculator", {
                'INPUT':dissolve_districts['OUTPUT'],
                'FIELD_NAME':'area_districts',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':8,
                'FIELD_PRECISION':0,
                'FORMULA':'round($area, 0)',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
        
        sum_line_polygons = processing.run("native:sumlinelengths", {
                'POLYGONS':area_districts['OUTPUT'],
                'LINES':parameters['INPUT2'],
                'LEN_FIELD':'dlugosc_drog',
                'COUNT_FIELD':'count',
                'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        saturation_lines = processing.run("native:fieldcalculator", {
                'INPUT': sum_line_polygons['OUTPUT'],
                'FIELD_NAME':'saturation_lines',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':8,
                'FIELD_PRECISION':0,
                'FORMULA':'("dlugosc_drog"*10000)/"area_districts"',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        lines_saturation_rating = processing.run("native:fieldcalculator", {
                'INPUT': saturation_lines['OUTPUT'],
                'FIELD_NAME':'o5',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':8,
                'FIELD_PRECISION':0,
                'FORMULA':'CASE WHEN "saturation_lines" >= 0 AND "saturation_lines" < 10 THEN 0 WHEN "saturation_lines" >= 10 AND "saturation_lines" < 20 THEN 1 WHEN "saturation_lines" >= 20 AND "saturation_lines" < 30 THEN 2 WHEN "saturation_lines" >= 30 AND "saturation_lines" < 40 THEN 3 WHEN "saturation_lines" >= 40 AND "saturation_lines" < 50 THEN 2 WHEN "saturation_lines" >= 50 AND "saturation_lines" < 60 THEN 1 WHEN "saturation_lines" >= 60 THEN 0 ELSE 0 END',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        join_plots = processing.run("native:joinattributestable", {
                'INPUT': districts['OUTPUT'],
                'FIELD':'districts',
                'INPUT_2': lines_saturation_rating['OUTPUT'],
                'FIELD_2':'districts',
                'FIELDS_TO_COPY':['o5'],
                'METHOD':1,
                'DISCARD_NONMATCHING':False,
                'PREFIX':'',
                'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
         
        # cleanig data
        
        drop_fields = processing.run("native:deletecolumn", {
                'INPUT': join_plots['OUTPUT'],
                'COLUMN':[''],
                'OUTPUT': parameters['OUTPUT']
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        
        
        
        
        return {'OUTPUT': drop_fields['OUTPUT']}
