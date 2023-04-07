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


class DzialkiPodobneProcessingAlgorithm(QgsProcessingAlgorithm):

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return DzialkiPodobneProcessingAlgorithm()

    def name(self):
        return 'podciborskitabelasiedem'

    def displayName(self):
        return self.tr('dzialki podobne (tabela 7)')

    def group(self):
        return self.tr('ocena ładu przestrzennego obszarów wiejskich')

    def groupId(self):
        return 'ocena ładu przestrzennego obszarów wiejskich'

    def shortHelpString(self):
        return self.tr("tabela 7")

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
        
        area_plot = processing.run("native:fieldcalculator", {
                'INPUT': parameters['INPUT'],
                'FIELD_NAME':'area',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':8,
                'FIELD_PRECISION':0,
                'FORMULA':'$area',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
        
        lines_from_plot_polygon_layer = processing.run("native:polygonstolines", {
                'INPUT': area_plot['OUTPUT'], 
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        length_lines_plot = processing.run("native:fieldcalculator", {
                'INPUT': lines_from_plot_polygon_layer['OUTPUT'],
                'FIELD_NAME':'length_lines_plot',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':8,
                'FIELD_PRECISION':0,
                'FORMULA':'$length',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        explode_lines_plot = processing.run("native:explodelines", {
                'INPUT': length_lines_plot['OUTPUT'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        length_exp_lines_plots = processing.run("native:fieldcalculator", {
                'INPUT': explode_lines_plot['OUTPUT'],
                'FIELD_NAME':'length_exp_lines_plots',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':8,
                'FIELD_PRECISION':0,
                'FORMULA':'$length',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        # script II part
        
        centroid_plot = processing.run("native:centroids", {
                'INPUT':area_plot['OUTPUT'],
                'ALL_PARTS':False,
                'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        centroid_line_plot = processing.run("native:centroids", {
                'INPUT':length_exp_lines_plots['OUTPUT'],
                'ALL_PARTS':False,
                'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        # script III part

        intersection_pt = processing.run("native:intersection", {
                'INPUT':centroid_line_plot['OUTPUT'],
                'OVERLAY':area_plot['OUTPUT'],
                'INPUT_FIELDS':[],
                'OVERLAY_FIELDS':[],
                'OVERLAY_FIELDS_PREFIX':'',
                'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        duplicates_pt = processing.run("native:fieldcalculator", {
                'INPUT': intersection_pt['OUTPUT'],
                'FIELD_NAME':'duplicates_pt',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':8,
                'FIELD_PRECISION':0,
                'FORMULA':'CASE WHEN "teryt" = "teryt_2" THEN 1 ELSE 0 END',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
        
        drops = processing.run("native:extractbyattribute", {
                'INPUT':duplicates_pt['OUTPUT'],
                'FIELD':'duplicates_pt',
                'OPERATOR':0,
                'VALUE':'0',
                'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        delete_geometries = processing.run("native:deleteduplicategeometries", 
                {'INPUT':drops['OUTPUT'],
                'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        sql_stack = processing.run("qgis:executesql", 
                {'INPUT_DATASOURCES': delete_geometries['OUTPUT'],
                'INPUT_QUERY':"SELECT teryt, area, area_2, length_lines_plot, length_exp_lines_plots FROM input1 UNION ALL SELECT teryt_2, area_2, area, length_lines_plot, length_exp_lines_plots FROM input1;",
                'INPUT_UID_FIELD':'',
                'INPUT_GEOMETRY_FIELD':'',
                'INPUT_GEOMETRY_TYPE':1,
                'INPUT_GEOMETRY_CRS':None,
                'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        area_class = processing.run("native:fieldcalculator", {
                'INPUT': sql_stack['OUTPUT'],
                'FIELD_NAME':'area_class',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':8,
                'FIELD_PRECISION':0,
                'FORMULA':'"area" * 0.1',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        diff_area = processing.run("native:fieldcalculator", {
                'INPUT': area_class['OUTPUT'],
                'FIELD_NAME':'diff_area',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':8,
                'FIELD_PRECISION':0,
                'FORMULA':'"area" - "area_2"',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        diff_clean = processing.run("native:fieldcalculator", {
                'INPUT': diff_area['OUTPUT'],
                'FIELD_NAME':'diff_clean',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':8,
                'FIELD_PRECISION':0,
                'FORMULA':'CASE WHEN "diff_area" >= 0 THEN "diff_area" ELSE "diff_area" * -1 END',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        bool_pairs = processing.run("native:fieldcalculator", {
                'INPUT': diff_clean['OUTPUT'],
                'FIELD_NAME':'bool_pairs',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':8,
                'FIELD_PRECISION':0,
                'FORMULA':'CASE WHEN "diff_clean" <= "area_class" THEN 0 ELSE 1 END',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        drop_other = processing.run("native:extractbyattribute", {
                'INPUT':bool_pairs['OUTPUT'],
                'FIELD':'bool_pairs',
                'OPERATOR':0,
                'VALUE':'0',
                'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        agg_sims = processing.run("native:aggregate", {
                'INPUT': drop_other['OUTPUT'],
                'GROUP_BY':'"teryt"',
                'AGGREGATES':[{'aggregate': 'first_value','delimiter': ',','input': '"teryt"','length': 254,'name': 'teryt','precision': 0,'type': 10},
                {'aggregate': 'first_value','delimiter': ',','input': '"length_lines_plot"','length': 1,'name': 'length_lines_plot','precision': 0,'type': 2},
                {'aggregate': 'sum','delimiter': ',','input': '"length_exp_lines_plots"','length': 0,'name': 'length_exp_lines_plots','precision': 0,'type': 2}],
                'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        percent_similar_plots = processing.run("native:fieldcalculator", {
                'INPUT': agg_sims['OUTPUT'],
                'FIELD_NAME':'percent_similar_plots',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':8,
                'FIELD_PRECISION':0,
                'FORMULA':'("length_exp_lines_plots"/"length_lines_plot")*100',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        similar_plots_assessment = processing.run("native:fieldcalculator", {
                'INPUT': percent_similar_plots['OUTPUT'],
                'FIELD_NAME':'similar_plots_assessment',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':8,
                'FIELD_PRECISION':0,
                'FORMULA':'CASE WHEN "percent_similar_plots" > 75 THEN 3 WHEN "percent_similar_plots" > 50 AND "percent_similar_plots" <= 75 THEN 2 WHEN "percent_similar_plots" > 25 AND "percent_similar_plots" <= 50 THEN 1 WHEN "percent_similar_plots" >= 0 AND "percent_similar_plots" <= 25 THEN 0 ELSE 0 END',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        join_evaluation = processing.run("native:joinattributestable", {
                'INPUT': parameters['INPUT'],
                'FIELD':'teryt',
                'INPUT_2': similar_plots_assessment['OUTPUT'],
                'FIELD_2':'teryt',
                'FIELDS_TO_COPY':['similar_plots_assessment'],
                'METHOD':1,
                'DISCARD_NONMATCHING':False,
                'PREFIX':'',
                'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        # cleanig data
        
        drop_fields = processing.run("native:deletecolumn", {
                'INPUT': join_evaluation['OUTPUT'],
                'COLUMN':['area'],
                'OUTPUT': parameters['OUTPUT']
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        return {'OUTPUT': drop_fields['OUTPUT']}
