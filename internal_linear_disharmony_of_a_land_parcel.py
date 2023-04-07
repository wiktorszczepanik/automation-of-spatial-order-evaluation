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
        
        
        # script I part
        
        area_plot = processing.run("native:fieldcalculator", {
                'INPUT': parameters['INPUT3'],
                'FIELD_NAME':'area_plot',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':8,
                'FIELD_PRECISION':0,
                'FORMULA':'$area',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        difference_sw_p = processing.run("native:difference", 
                {'INPUT':area_plot['OUTPUT'],
                'OVERLAY':parameters['INPUT2'],
                'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        area_plot_sw_p = processing.run("native:fieldcalculator", {
                'INPUT': difference_sw_p['OUTPUT'],
                'FIELD_NAME':'area_plot_sw_p',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':8,
                'FIELD_PRECISION':0,
                'FORMULA':'$area',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        area_use_sw_p = processing.run("native:fieldcalculator", {
                'INPUT': area_plot_sw_p['OUTPUT'],
                'FIELD_NAME':'area_use_sw_p',
                'FIELD_TYPE':0,
                'FIELD_LENGTH':8,
                'FIELD_PRECISION':0,
                'FORMULA':'100-(round((("area_plot_sw_p"/"area_plot")*100), 3))',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        join_polygons_sw_p = processing.run("native:joinattributestable", {
                'INPUT': area_plot['OUTPUT'],
                'FIELD':'teryt',
                'INPUT_2': area_use_sw_p['OUTPUT'],
                'FIELD_2':'teryt',
                'FIELDS_TO_COPY':['teryt', 'area_use_sw_p'],
                'METHOD':1,
                'DISCARD_NONMATCHING':False,
                'PREFIX':'',
                'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
        
        dysharmony_assessment_plot = processing.run("native:fieldcalculator", {
                'INPUT': join_polygons_sw_p['OUTPUT'],
                'FIELD_NAME':'o6',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':8,
                'FIELD_PRECISION':0,
                'FORMULA':'CASE WHEN "area_use_sw_p" >= 0 AND "area_use_sw_p" < 0.1 THEN 3 WHEN "area_use_sw_p" >= 0.1 AND "area_use_sw_p" < 1 THEN 2 WHEN "area_use_sw_p" >= 1 AND "area_use_sw_p" < 2.2 THEN 1 ELSE 0 END',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
        
        # cleanig data
        
        drop_fields = processing.run("native:deletecolumn", {
                'INPUT': dysharmony_assessment_plot['OUTPUT'],
                'COLUMN':['area_plot', 'teryt_2'],
                'OUTPUT': parameters['OUTPUT']
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        
        
        
        
        return {'OUTPUT': drop_fields['OUTPUT']}
