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
        
        
        # skrypt część I
        
        kierunek = processing.run("native:fieldcalculator", {
                'INPUT': parameters['INPUT'],
                'FIELD_NAME':'kierunek',
                'FIELD_TYPE':0,
                'FIELD_LENGTH':3,
                'FIELD_PRECISION':0,
                'FORMULA':'main_angle($geometry)',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        kierunek_clean = processing.run("native:fieldcalculator", {
                'INPUT': kierunek['OUTPUT'],
                'FIELD_NAME':'kierunek_clean',
                'FIELD_TYPE':0,
                'FIELD_LENGTH':3,
                'FIELD_PRECISION':0,
                'FORMULA':'CASE WHEN "kierunek" >= 180 THEN "kierunek" - 180  ELSE "kierunek" END',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        lines_from_polygon_layer = processing.run("native:polygonstolines", {
                'INPUT': kierunek_clean['OUTPUT'], 
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        lines_length = processing.run("native:fieldcalculator", {
                'INPUT': lines_from_polygon_layer['OUTPUT'],
                'FIELD_NAME':'lines_length',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':50,
                'FIELD_PRECISION':0,
                'FORMULA':'$length',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        explode_lines = processing.run("native:explodelines", {
                'INPUT': lines_length['OUTPUT'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        marge_lines = processing.run("lftools:directionalmerge", {
                'LINES': explode_lines['OUTPUT'],
                'TYPE':0,
                'ANGLE':1,
                'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        one_line_length = processing.run("native:fieldcalculator", {
                'INPUT': marge_lines['OUTPUT'],
                'FIELD_NAME':'one_line_length',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':50,
                'FIELD_PRECISION':0,
                'FORMULA':'$length',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        procentage_longest = processing.run("native:fieldcalculator", {
                'INPUT': one_line_length['OUTPUT'],
                'FIELD_NAME':'procentage_longest',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':50,
                'FIELD_PRECISION':0,
                'FORMULA':'(maximum("one_line_length", "teryt") / "lines_length") * 100',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        for_delete = processing.run("native:fieldcalculator", {
                'INPUT': procentage_longest['OUTPUT'],
                'FIELD_NAME':'for_delete',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':50,
                'FIELD_PRECISION':0,
                'FORMULA':'CASE WHEN "procentage_longest" >= 25 THEN 0 ELSE 1 END',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        agg_geom_lines = processing.run("native:aggregate", {
                'INPUT': for_delete['OUTPUT'],
                'GROUP_BY':'"teryt"',
                'AGGREGATES':[{'aggregate': 'first_value','delimiter': ',','input': '"teryt"','length': 254,'name': 'teryt','precision': 0,'type': 10},
                {'aggregate': 'first_value','delimiter': ',','input': '"kierunek"','length': 0,'name': 'kierunek','precision': 0,'type': 3},
                {'aggregate': 'first_value','delimiter': ',','input': '"kierunek_clean"','length': 0,'name': 'kierunek_clean','precision': 0,'type': 3},
                {'aggregate': 'first_value','delimiter': ',','input': '"lines_length"','length': 0,'name': 'lines_length','precision': 0,'type': 2},
                {'aggregate': 'first_value','delimiter': ',','input': '"one_line_length"','length': 0,'name': 'one_line_length','precision': 0,'type': 2},
                {'aggregate': 'first_value','delimiter': ',','input': '"procentage_longest"','length': 0,'name': 'procentage_longest','precision': 0,'type': 2},
                {'aggregate': 'first_value','delimiter': ',','input': '"for_delete"','length': 1,'name': 'for_delete','precision': 0,'type': 2}],
                'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        join_oceny = processing.run("native:joinattributestable", {
                'INPUT': parameters['INPUT'],
                'FIELD':'teryt',
                'INPUT_2': agg_geom_lines['OUTPUT'],
                'FIELD_2':'teryt',
                'FIELDS_TO_COPY':['kierunek_clean', 'for_delete'],
                'METHOD':1,
                'DISCARD_NONMATCHING':False,
                'PREFIX':'',
                'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        ocena_kierunek = processing.run("native:fieldcalculator", {
                'INPUT': join_oceny['OUTPUT'],
                'FIELD_NAME':'ocena_kierunek',
                'FIELD_TYPE':0,
                'FIELD_LENGTH':3,
                'FIELD_PRECISION':0,
                'FORMULA':'CASE WHEN ("kierunek_clean" >= 0 AND "kierunek_clean" <= 22) OR ("kierunek_clean" > 157 AND "kierunek_clean" <= 180) THEN 3 WHEN ("kierunek_clean" > 22 AND "kierunek_clean" <= 67) OR ("kierunek_clean" > 112 AND "kierunek_clean" <= 157) THEN 2 WHEN "kierunek_clean" > 67 AND "kierunek_clean" <= 112 THEN 1 ELSE 0 END',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        ocena_kierunek_poprawa = processing.run("native:fieldcalculator", {
                'INPUT': ocena_kierunek['OUTPUT'],
                'FIELD_NAME':'ocena_kierunek',
                'FIELD_TYPE':0,
                'FIELD_LENGTH':3,
                'FIELD_PRECISION':0,
                'FORMULA':'if("for_delete" = 1, "ocena_kierunek" = 0, "ocena_kierunek")',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
        
        
        
        
        drop_fields = processing.run("native:deletecolumn", {
                'INPUT': ocena_kierunek_poprawa['OUTPUT'],
                'COLUMN':['', ''],
                'OUTPUT': parameters['OUTPUT']
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        
        
        
        
        return {'OUTPUT': drop_fields['OUTPUT']}
