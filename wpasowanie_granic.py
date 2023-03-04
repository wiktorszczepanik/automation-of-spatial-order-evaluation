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


class WpasowanieGranicProcessingAlgorithm(QgsProcessingAlgorithm):

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return WpasowanieGranicProcessingAlgorithm()

    def name(self):
        return 'podciborskitabeladwa'

    def displayName(self):
        return self.tr('wpasowanie granic (tabela 2)')

    def group(self):
        return self.tr('ocena ładu przestrzennego obszarów wiejskich')

    def groupId(self):
        return 'ocena ładu przestrzennego obszarów wiejskich'

    def shortHelpString(self):
        return self.tr("tabela 2")

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
                self.tr('Niezmienniki przestrzenne'),
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
                
        # skrypt część IV
        
        row_num_poly = processing.run("native:fieldcalculator", {
                'INPUT': parameters['INPUT3'],
                'FIELD_NAME':'row_num_poly',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':8,
                'FIELD_PRECISION':0,
                'FORMULA':'@row_number',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
        
        pol_to_lines = processing.run("native:polygonstolines", {
                'INPUT':row_num_poly['OUTPUT'],
                'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        dlugosc_old = processing.run("native:fieldcalculator", {
                'INPUT': pol_to_lines['OUTPUT'],
                'FIELD_NAME':'dlugosc_old',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':8,
                'FIELD_PRECISION':0,
                'FORMULA':'$length',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        explode_lines = processing.run("native:explodelines", {
                'INPUT': dlugosc_old['OUTPUT'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
#dziala                
        split_lines = processing.run("native:splitlinesbylength", {
                'INPUT':explode_lines['OUTPUT'],
                'LENGTH':5,
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        spatial_index_one = processing.run("native:createspatialindex", {
                'INPUT': split_lines['OUTPUT']}, is_child_algorithm=True, context=context, feedback=feedback)
                
        selection_and_delete = processing.run("native:extractbylocation", {
                'INPUT':split_lines['OUTPUT'],
                'PREDICATE':[0],
                'INTERSECT':parameters['INPUT2'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
        


#bug        
        dlugosc_new = processing.run("native:fieldcalculator", {
                'INPUT': selection_and_delete['OUTPUT'],
                'FIELD_NAME':'dlugosc_new',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':8,
                'FIELD_PRECISION':0,
                'FORMULA':'$length',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        aggregate_geom = processing.run("native:aggregate", {
                'INPUT': dlugosc_new['OUTPUT'],
                'GROUP_BY':'"row_num_poly"',
                'AGGREGATES':[{'aggregate': 'first_value','delimiter': ',','input': '"teryt"','length': 254,'name': 'teryt','precision': 0,'type': 10},
                {'aggregate': 'first_value','delimiter': ',','input': '"row_num_poly"','length': 0,'name': 'row_num_poly','precision': 0,'type': 2},
                {'aggregate': 'first_value','delimiter': ',','input': '"dlugosc_old"','length': 50,'name': 'dlugosc_old','precision': 0,'type': 2},
                {'aggregate': 'sum','delimiter': ',','input': '"dlugosc_new"','length': 0,'name': 'dlugosc_new','precision': 0,'type': 2}],
                'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        join_for_polygons = processing.run("native:joinattributestable", {
                'INPUT': row_num_poly['OUTPUT'],
                'FIELD':'row_num_poly',
                'INPUT_2': aggregate_geom['OUTPUT'],
                'FIELD_2':'row_num_poly',
                'FIELDS_TO_COPY':['dlugosc_old', 'dlugosc_new'],
                'METHOD':1,
                'DISCARD_NONMATCHING':False,
                'PREFIX':'',
                'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        param_wpasowanie_granic = processing.run("native:fieldcalculator", {
                'INPUT': join_for_polygons['OUTPUT'],
                'FIELD_NAME':'param_wpasowanie_granic',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':8,
                'FIELD_PRECISION':0,
                'FORMULA':'("dlugosc_new"/"dlugosc_old")*100',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        ocena_wpasowania = processing.run("native:fieldcalculator", {
                'INPUT': param_wpasowanie_granic['OUTPUT'],
                'FIELD_NAME':'ocena_wpasowania',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':8,
                'FIELD_PRECISION':0,
                'FORMULA':'CASE WHEN "param_wpasowanie_granic" < 25 THEN 0 WHEN "param_wpasowanie_granic" >= 25 AND "param_wpasowanie_granic" < 50 THEN 1 WHEN "param_wpasowanie_granic" >= 50 AND "param_wpasowanie_granic" < 75 THEN 2 WHEN "param_wpasowanie_granic" >= 75 THEN 3 END',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)

        
        
        drop_fields = processing.run("native:deletecolumn", {
                'INPUT': ocena_wpasowania['OUTPUT'],
                'COLUMN':['vertex_index', 'vertex_part', 'vertex_part_index', 'distance', 'angle', 'xy_id', 'row_num_poly', 'dlugosc_old', 'dlugosc_new', 'param_wpasowanie_granic'],
                'OUTPUT': parameters['OUTPUT']
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        
        
        
        
        return {'OUTPUT': drop_fields['OUTPUT']}
