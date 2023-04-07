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


class PotrzebyFotoFizjologiczneProcessingAlgorithm(QgsProcessingAlgorithm):

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return PotrzebyFotoFizjologiczneProcessingAlgorithm()

    def name(self):
        return 'podciborskitabelacztery'

    def displayName(self):
        return self.tr('potrzeby fotofizjologiczne (tabela 4)')

    def group(self):
        return self.tr('ocena ładu przestrzennego obszarów wiejskich')

    def groupId(self):
        return 'ocena ładu przestrzennego obszarów wiejskich'

    def shortHelpString(self):
        return self.tr("tabela 4")

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
        
        direction_plot = processing.run("native:fieldcalculator", {
                'INPUT': parameters['INPUT'],
                'FIELD_NAME':'direction_plot',
                'FIELD_TYPE':0,
                'FIELD_LENGTH':3,
                'FIELD_PRECISION':0,
                'FORMULA':'main_angle($geometry)',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        direction_plot_clean = processing.run("native:fieldcalculator", {
                'INPUT': direction_plot['OUTPUT'],
                'FIELD_NAME':'direction_plot_clean',
                'FIELD_TYPE':0,
                'FIELD_LENGTH':3,
                'FIELD_PRECISION':0,
                'FORMULA':'CASE WHEN "direction_plot" >= 180 THEN "direction_plot" - 180  ELSE "direction_plot" END',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        lines_polygon_layer = processing.run("native:polygonstolines", {
                'INPUT': direction_plot_clean['OUTPUT'], 
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        lines_length = processing.run("native:fieldcalculator", {
                'INPUT': lines_polygon_layer['OUTPUT'],
                'FIELD_NAME':'lines_length',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':50,
                'FIELD_PRECISION':0,
                'FORMULA':'$length',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        explode_line = processing.run("native:explodelines", {
                'INPUT': lines_length['OUTPUT'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        marge_line = processing.run("lftools:directionalmerge", {
                'LINES': explode_line['OUTPUT'],
                'TYPE':0,
                'ANGLE':1,
                'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        one_line_length = processing.run("native:fieldcalculator", {
                'INPUT': marge_line['OUTPUT'],
                'FIELD_NAME':'one_line_length',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':50,
                'FIELD_PRECISION':0,
                'FORMULA':'$length',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        percentage_long = processing.run("native:fieldcalculator", {
                'INPUT': one_line_length['OUTPUT'],
                'FIELD_NAME':'percentage_long',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':50,
                'FIELD_PRECISION':0,
                'FORMULA':'(maximum("one_line_length", "teryt") / "lines_length") * 100',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        for_delete = processing.run("native:fieldcalculator", {
                'INPUT': percentage_long['OUTPUT'],
                'FIELD_NAME':'for_delete',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':50,
                'FIELD_PRECISION':0,
                'FORMULA':'CASE WHEN "percentage_long" >= 25 THEN 0 ELSE 1 END',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        agg_geom_line = processing.run("native:aggregate", {
                'INPUT': for_delete['OUTPUT'],
                'GROUP_BY':'"teryt"',
                'AGGREGATES':[{'aggregate': 'first_value','delimiter': ',','input': '"teryt"','length': 254,'name': 'teryt','precision': 0,'type': 10},
                {'aggregate': 'first_value','delimiter': ',','input': '"direction_plot"','length': 0,'name': 'direction_plot','precision': 0,'type': 3},
                {'aggregate': 'first_value','delimiter': ',','input': '"direction_plot_clean"','length': 0,'name': 'direction_plot_clean','precision': 0,'type': 3},
                {'aggregate': 'first_value','delimiter': ',','input': '"lines_length"','length': 0,'name': 'lines_length','precision': 0,'type': 2},
                {'aggregate': 'first_value','delimiter': ',','input': '"one_line_length"','length': 0,'name': 'one_line_length','precision': 0,'type': 2},
                {'aggregate': 'first_value','delimiter': ',','input': '"percentage_long"','length': 0,'name': 'percentage_long','precision': 0,'type': 2},
                {'aggregate': 'first_value','delimiter': ',','input': '"for_delete"','length': 1,'name': 'for_delete','precision': 0,'type': 2}],
                'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        join_evaluation = processing.run("native:joinattributestable", {
                'INPUT': parameters['INPUT'],
                'FIELD':'teryt',
                'INPUT_2': agg_geom_line['OUTPUT'],
                'FIELD_2':'teryt',
                'FIELDS_TO_COPY':['direction_plot_clean', 'for_delete'],
                'METHOD':1,
                'DISCARD_NONMATCHING':False,
                'PREFIX':'',
                'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        direction_plot_evaluation = processing.run("native:fieldcalculator", {
                'INPUT': join_evaluation['OUTPUT'],
                'FIELD_NAME':'direction_plot_evaluation',
                'FIELD_TYPE':0,
                'FIELD_LENGTH':3,
                'FIELD_PRECISION':0,
                'FORMULA':'CASE WHEN ("direction_plot_clean" >= 0 AND "direction_plot_clean" <= 22) OR ("direction_plot_clean" > 157 AND "direction_plot_clean" <= 180) THEN 3 WHEN ("direction_plot_clean" > 22 AND "direction_plot_clean" <= 67) OR ("direction_plot_clean" > 112 AND "direction_plot_clean" <= 157) THEN 2 WHEN "direction_plot_clean" > 67 AND "direction_plot_clean" <= 112 THEN 1 ELSE 0 END',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        direction_plot_evaluation_secound_parse = processing.run("native:fieldcalculator", {
                'INPUT': direction_plot_evaluation['OUTPUT'],
                'FIELD_NAME':'direction_plot_evaluation',
                'FIELD_TYPE':0,
                'FIELD_LENGTH':3,
                'FIELD_PRECISION':0,
                'FORMULA':'if("for_delete" = 1, "direction_plot_evaluation" = 0, "direction_plot_evaluation")',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
        
        
        # cleanig data
        
        drop_fields = processing.run("native:deletecolumn", {
                'INPUT': direction_plot_evaluation_secound_parse['OUTPUT'],
                'COLUMN':['', ''],
                'OUTPUT': parameters['OUTPUT']
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        
        
        
        
        return {'OUTPUT': drop_fields['OUTPUT']}
