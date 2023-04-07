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


class KalkulacjaZbiorczaProcessingAlgorithm(QgsProcessingAlgorithm):

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return KalkulacjaZbiorczaProcessingAlgorithm()

    def name(self):
        return 'podciborskitabeladziesiec'

    def displayName(self):
        return self.tr('kalkulacja zbiorcza (tabela 10)')

    def group(self):
        return self.tr('ocena ładu przestrzennego obszarów wiejskich')

    def groupId(self):
        return 'ocena ładu przestrzennego obszarów wiejskich'

    def shortHelpString(self):
        return self.tr("tabela 10")

    def initAlgorithm(self, config=None):
        
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                'INPUT1',
                self.tr('Ocena nr.1'),
                types=[QgsProcessing.TypeVectorPolygon]
            )
        )
        
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                'INPUT2',
                self.tr('Ocena nr.2'),
                types=[QgsProcessing.TypeVectorPolygon]
            )
        )
        
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                'INPUT3',
                self.tr('Ocena nr.3'),
                types=[QgsProcessing.TypeVectorPolygon]
            )
        )
        
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                'INPUT4',
                self.tr('Ocena nr.4'),
                types=[QgsProcessing.TypeVectorPolygon]
            )
        )
        
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                'INPUT5',
                self.tr('Ocena nr.5'),
                types=[QgsProcessing.TypeVectorPolygon]
            )
        )
        
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                'INPUT6',
                self.tr('Ocena nr.6'),
                types=[QgsProcessing.TypeVectorPolygon]
            )
        )
        
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                'INPUT7',
                self.tr('Ocena nr.7'),
                types=[QgsProcessing.TypeVectorPolygon]
            )
        )
        
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                'INPUT8',
                self.tr('Ocena nr.8'),
                types=[QgsProcessing.TypeVectorPolygon]
            )
        )
        
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                'INPUT9',
                self.tr('Ocena nr.9'),
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
        
        marge_layers = processing.run("native:mergevectorlayers", {
                'LAYERS':[parameters['INPUT1'], parameters['INPUT2'], parameters['INPUT3'], parameters['INPUT4'], parameters['INPUT5'], parameters['INPUT6'], parameters['INPUT7'], parameters['INPUT8'], parameters['INPUT9']],
                'CRS':QgsCoordinateReferenceSystem('EPSG:2178'),
                'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        aggregate_evaluation = processing.run("native:aggregate", {
                'INPUT': marge_layers['OUTPUT'],
                'GROUP_BY':'"teryt"',
                'AGGREGATES':[{'aggregate': 'first_value','delimiter': ',','input': '"teryt"','length': 254,'name': 'teryt','precision': 0,'type': 10},
                {'aggregate': 'sum','delimiter': ',','input': '"oceny_ksztaltu"','length': 0,'name': 'oceny_ksztaltu','precision': 0,'type': 2},
                {'aggregate': 'sum','delimiter': ',','input': '"ocena_wpasowania"','length': 50,'name': 'ocena_wpasowania','precision': 0,'type': 2},
                {'aggregate': 'sum','delimiter': ',','input': '"ocena_prostoliniowosci"','length': 0,'name': 'ocena_prostoliniowosci','precision': 0,'type': 2},
                {'aggregate': 'sum','delimiter': ',','input': '"ocena_kierunek"','length': 0,'name': 'ocena_kierunek','precision': 0,'type': 2},
                {'aggregate': 'sum','delimiter': ',','input': '"ocena_nasycenia"','length': 0,'name': 'ocena_nasycenia','precision': 0,'type': 2},
                {'aggregate': 'sum','delimiter': ',','input': '"ocena_dysharmonia"','length': 10,'name': 'ocena_dysharmonia','precision': 0,'type': 2},
                {'aggregate': 'sum','delimiter': ',','input': '"ocena_dzialki_podobne"','length': 7,'name': 'ocena_dzialki_podobne','precision': 0,'type': 2},
                {'aggregate': 'sum','delimiter': ',','input': '"ocena_harmonijnosci"','length': 7,'name': 'ocena_harmonijnosci','precision': 0,'type': 2},
                {'aggregate': 'sum','delimiter': ',','input': '"ocena_jednorodnosc"','length': 1,'name': 'ocena_jednorodnosc','precision': 0,'type': 2}],
                'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        sum_evaluation = processing.run("native:fieldcalculator", {
                'INPUT': aggregate_evaluation['OUTPUT'],
                'FIELD_NAME':'sum_evaluation',
                'FIELD_TYPE':1,
                'FIELD_LENGTH':8,
                'FIELD_PRECISION':0,
                'FORMULA':'"oceny_ksztaltu" + "ocena_wpasowania" + "ocena_prostoliniowosci" + "ocena_kierunek" + "ocena_nasycenia" + "ocena_dysharmonia" + "ocena_dzialki_podobne" + "ocena_harmonijnosci" + "ocena_jednorodnosc"',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        # cleanig data
        
        drop_fields = processing.run("native:deletecolumn", {
                'INPUT': sum_evaluation['OUTPUT'],
                'COLUMN':[''],
                'OUTPUT': parameters['OUTPUT']
                }, is_child_algorithm=True, context=context, feedback=feedback)
                
        return {'OUTPUT': drop_fields['OUTPUT']}
