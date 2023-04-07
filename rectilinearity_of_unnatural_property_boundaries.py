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


class ProstoliniowoscNienaturalnychProcessingAlgorithm(QgsProcessingAlgorithm):

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return ProstoliniowoscNienaturalnychProcessingAlgorithm()

    def name(self):
        return 'podciborskitabelatrzy'

    def displayName(self):
        return self.tr('prostoliniowość nienaturalnych (tabela 3)')

    def group(self):
        return self.tr('ocena ładu przestrzennego obszarów wiejskich')

    def groupId(self):
        return 'ocena ładu przestrzennego obszarów wiejskich'

    def shortHelpString(self):
        return self.tr("tabela 3")

    def initAlgorithm(self, config=None):
        
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                'INPUT',
                self.tr('Działki ewidencyjne'),
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
        
        line_polygon_layer = processing.run("native:polygonstolines", {
                'INPUT': parameters['INPUT'], 
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        num_id = processing.run("native:fieldcalculator", {
                'INPUT': line_polygon_layer['OUTPUT'],
                'FIELD_NAME':'num_id',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':0,
                'FIELD_PRECISION':0,
                'FORMULA':'$id',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        explode_line = processing.run("native:explodelines", {
                'INPUT': num_id['OUTPUT'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
            
        marge_line = processing.run("lftools:directionalmerge", {
                'LINES': explode_line['OUTPUT'],
                'TYPE':0,
                'ANGLE':2,
                'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        # script II part
                
        agg_str_line = processing.run("native:aggregate", {
                'INPUT': marge_line['OUTPUT'],
                'GROUP_BY':'"num_id"',
                'AGGREGATES':[{'aggregate': 'first_value','delimiter': ',','input': '"teryt"','length': 254,'name': 'teryt','precision': 0,'type': 10},
                {'aggregate': 'first_value','delimiter': ',','input': '"num_id"','length': 0,'name': 'num_id','precision': 0,'type': 2},
                {'aggregate': 'count','delimiter': ',','input': '"num_id"','length': 50,'name': 'liczba_zalaman','precision': 0,'type': 2}],
                'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
                
        str_evaluation = processing.run("native:fieldcalculator", {
                'INPUT': agg_str_line['OUTPUT'],
                'FIELD_NAME':'str_evaluation',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':0,
                'FIELD_PRECISION':0,
                'FORMULA':'CASE WHEN "liczba_zalaman" = 4 THEN 3 WHEN "liczba_zalaman" = 3 OR "liczba_zalaman" = 5 THEN 2 WHEN "liczba_zalaman" >= 6 AND "liczba_zalaman" <= 10 THEN 1 WHEN "liczba_zalaman" > 10 THEN 0 END',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        join_evaluation = processing.run("native:joinattributestable", {
                'INPUT': parameters['INPUT'],
                'FIELD':'teryt',
                'INPUT_2': str_evaluation['OUTPUT'],
                'FIELD_2':'teryt',
                'FIELDS_TO_COPY':['str_evaluation'],
                'METHOD':1,
                'DISCARD_NONMATCHING':False,
                'PREFIX':'',
                'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
        
        # cleanig data
        
        drop_fields = processing.run("native:deletecolumn", {
                'INPUT': join_evaluation['OUTPUT'],
                'COLUMN':['num_id'],
                'OUTPUT': parameters['OUTPUT']
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        
        
        
        
        return {'OUTPUT': drop_fields['OUTPUT']}
