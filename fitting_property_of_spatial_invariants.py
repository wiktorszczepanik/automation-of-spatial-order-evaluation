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
                        
        # script I part
        
        row_num_poly = processing.run("native:fieldcalculator", {
                'INPUT': parameters['INPUT3'],
                'FIELD_NAME':'row_num_poly',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':8,
                'FIELD_PRECISION':0,
                'FORMULA':'@row_number',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
        
        pol_to_line = processing.run("native:polygonstolines", {
                'INPUT':row_num_poly['OUTPUT'],
                'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        length_plot = processing.run("native:fieldcalculator", {
                'INPUT': pol_to_line['OUTPUT'],
                'FIELD_NAME':'length_plot',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':8,
                'FIELD_PRECISION':0,
                'FORMULA':'$length',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        explode_line = processing.run("native:explodelines", {
                'INPUT': length_plot['OUTPUT'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                       
        split_line = processing.run("native:splitlinesbylength", {
                'INPUT':explode_line['OUTPUT'],
                'LENGTH':5,
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        spatial_index_one = processing.run("native:createspatialindex", {
                'INPUT': split_line['OUTPUT']}, is_child_algorithm=True, context=context, feedback=feedback)
                
        selection_and_delete = processing.run("native:extractbylocation", {
                'INPUT':split_line['OUTPUT'],
                'PREDICATE':[0],
                'INTERSECT':parameters['INPUT2'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
          
        length_new_plot = processing.run("native:fieldcalculator", {
                'INPUT': selection_and_delete['OUTPUT'],
                'FIELD_NAME':'length_new_plot',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':8,
                'FIELD_PRECISION':0,
                'FORMULA':'$length',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        aggregate_geom = processing.run("native:aggregate", {
                'INPUT': length_new_plot['OUTPUT'],
                'GROUP_BY':'"row_num_poly"',
                'AGGREGATES':[{'aggregate': 'first_value','delimiter': ',','input': '"teryt"','length': 254,'name': 'teryt','precision': 0,'type': 10},
                {'aggregate': 'first_value','delimiter': ',','input': '"row_num_poly"','length': 0,'name': 'row_num_poly','precision': 0,'type': 2},
                {'aggregate': 'first_value','delimiter': ',','input': '"length_plot"','length': 50,'name': 'length_plot','precision': 0,'type': 2},
                {'aggregate': 'sum','delimiter': ',','input': '"length_new_plot"','length': 0,'name': 'length_new_plot','precision': 0,'type': 2}],
                'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        join_f_polygons = processing.run("native:joinattributestable", {
                'INPUT': row_num_poly['OUTPUT'],
                'FIELD':'row_num_poly',
                'INPUT_2': aggregate_geom['OUTPUT'],
                'FIELD_2':'row_num_poly',
                'FIELDS_TO_COPY':['length_plot', 'length_new_plot'],
                'METHOD':1,
                'DISCARD_NONMATCHING':False,
                'PREFIX':'',
                'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        border_fit = processing.run("native:fieldcalculator", {
                'INPUT': join_f_polygons['OUTPUT'],
                'FIELD_NAME':'border_fit',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':8,
                'FIELD_PRECISION':0,
                'FORMULA':'("length_new_plot"/"length_plot")*100',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        fit_evaluation = processing.run("native:fieldcalculator", {
                'INPUT': border_fit['OUTPUT'],
                'FIELD_NAME':'fit_evaluation',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':8,
                'FIELD_PRECISION':0,
                'FORMULA':'CASE WHEN "border_fit" < 25 THEN 0 WHEN "border_fit" >= 25 AND "border_fit" < 50 THEN 1 WHEN "border_fit" >= 50 AND "border_fit" < 75 THEN 2 WHEN "border_fit" >= 75 THEN 3 END',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)

        # cleanig data
        
        drop_fields = processing.run("native:deletecolumn", {
                'INPUT': fit_evaluation['OUTPUT'],
                'COLUMN':['vertex_index', 'vertex_part', 'vertex_part_index', 'distance', 'angle', 'xy_id', 'row_num_poly', 'length_plot', 'length_new_plot', 'border_fit'],
                'OUTPUT': parameters['OUTPUT']
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        
        
        
        
        return {'OUTPUT': drop_fields['OUTPUT']}
