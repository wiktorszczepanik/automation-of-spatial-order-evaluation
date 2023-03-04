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
        
        
        # skrypt część I
        
        powierzchnia_pol = processing.run("native:fieldcalculator", {
                'INPUT': parameters['INPUT'],
                'FIELD_NAME':'area',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':8,
                'FIELD_PRECISION':0,
                'FORMULA':'$area',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
        
        lines_from_polygon_layer = processing.run("native:polygonstolines", {
                'INPUT': powierzchnia_pol['OUTPUT'], 
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        dlugosc_obwod = processing.run("native:fieldcalculator", {
                'INPUT': lines_from_polygon_layer['OUTPUT'],
                'FIELD_NAME':'dlugosc_obwod',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':8,
                'FIELD_PRECISION':0,
                'FORMULA':'$length',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        explode_lines = processing.run("native:explodelines", {
                'INPUT': dlugosc_obwod['OUTPUT'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        dlugosc_line = processing.run("native:fieldcalculator", {
                'INPUT': explode_lines['OUTPUT'],
                'FIELD_NAME':'dlugosc_line',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':8,
                'FIELD_PRECISION':0,
                'FORMULA':'$length',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        # skrypt część II
        
        centroid_pol = processing.run("native:centroids", {
                'INPUT':powierzchnia_pol['OUTPUT'],
                'ALL_PARTS':False,
                'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        centroid_line = processing.run("native:centroids", {
                'INPUT':dlugosc_line['OUTPUT'],
                'ALL_PARTS':False,
                'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        # skrypt część III

        intersection_pt = processing.run("native:intersection", {
                'INPUT':centroid_line['OUTPUT'],
                'OVERLAY':powierzchnia_pol['OUTPUT'],
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
                'INPUT_QUERY':"SELECT teryt, area, area_2, dlugosc_obwod, dlugosc_line FROM input1 UNION ALL SELECT teryt_2, area_2, area, dlugosc_obwod, dlugosc_line FROM input1;",
                'INPUT_UID_FIELD':'',
                'INPUT_GEOMETRY_FIELD':'',
                'INPUT_GEOMETRY_TYPE':1,
                'INPUT_GEOMETRY_CRS':None,
                'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        klasy_pow = processing.run("native:fieldcalculator", {
                'INPUT': sql_stack['OUTPUT'],
                'FIELD_NAME':'klasy_pow',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':8,
                'FIELD_PRECISION':0,
                'FORMULA':'"area" * 0.1',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        diff_pow = processing.run("native:fieldcalculator", {
                'INPUT': klasy_pow['OUTPUT'],
                'FIELD_NAME':'diff_pow',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':8,
                'FIELD_PRECISION':0,
                'FORMULA':'"area" - "area_2"',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        diff_clean = processing.run("native:fieldcalculator", {
                'INPUT': diff_pow['OUTPUT'],
                'FIELD_NAME':'diff_clean',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':8,
                'FIELD_PRECISION':0,
                'FORMULA':'CASE WHEN "diff_pow" >= 0 THEN "diff_pow" ELSE "diff_pow" * -1 END',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        bool_pairs = processing.run("native:fieldcalculator", {
                'INPUT': diff_clean['OUTPUT'],
                'FIELD_NAME':'bool_pairs',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':8,
                'FIELD_PRECISION':0,
                'FORMULA':'CASE WHEN "diff_clean" <= "klasy_pow" THEN 0 ELSE 1 END',
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
                {'aggregate': 'first_value','delimiter': ',','input': '"dlugosc_obwod"','length': 1,'name': 'dlugosc_obwod','precision': 0,'type': 2},
                {'aggregate': 'sum','delimiter': ',','input': '"dlugosc_line"','length': 0,'name': 'dlugosc_line','precision': 0,'type': 2}],
                'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        proc_dzialki_podobne = processing.run("native:fieldcalculator", {
                'INPUT': agg_sims['OUTPUT'],
                'FIELD_NAME':'proc_dzialki_podobne',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':8,
                'FIELD_PRECISION':0,
                'FORMULA':'("dlugosc_line"/"dlugosc_obwod")*100',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        ocena_dzialki_podobne = processing.run("native:fieldcalculator", {
                'INPUT': proc_dzialki_podobne['OUTPUT'],
                'FIELD_NAME':'ocena_dzialki_podobne',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':8,
                'FIELD_PRECISION':0,
                'FORMULA':'CASE WHEN "proc_dzialki_podobne" > 75 THEN 3 WHEN "proc_dzialki_podobne" > 50 AND "proc_dzialki_podobne" <= 75 THEN 2 WHEN "proc_dzialki_podobne" > 25 AND "proc_dzialki_podobne" <= 50 THEN 1 WHEN "proc_dzialki_podobne" >= 0 AND "proc_dzialki_podobne" <= 25 THEN 0 ELSE 0 END',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        join_wynik = processing.run("native:joinattributestable", {
                'INPUT': parameters['INPUT'],
                'FIELD':'teryt',
                'INPUT_2': ocena_dzialki_podobne['OUTPUT'],
                'FIELD_2':'teryt',
                'FIELDS_TO_COPY':['ocena_dzialki_podobne'],
                'METHOD':1,
                'DISCARD_NONMATCHING':False,
                'PREFIX':'',
                'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
                
        
        drop_fields = processing.run("native:deletecolumn", {
                'INPUT': join_wynik['OUTPUT'],
                'COLUMN':['area'],
                'OUTPUT': parameters['OUTPUT']
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        return {'OUTPUT': drop_fields['OUTPUT']}
