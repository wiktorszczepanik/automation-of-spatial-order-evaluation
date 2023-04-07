# -*- coding: utf-8 -*-

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsExpression
import processing


class HarmonijnoscPrzestrzennaUzytkowania(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer('dziakiewidencyjne', 'Działki ewidencyjne', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('uykigruntowe', 'Użyki gruntowe', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Wynik', 'wynik', optional=True, type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        feedback = QgsProcessingMultiStepFeedback(10, model_feedback)
        results = {}
        outputs = {}

        # script I part
        
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'id_plots',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 1,  
            'FORMULA': '$id',
            'INPUT': parameters['dziakiewidencyjne'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['id_plots'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'INPUT': outputs['id_plots']['OUTPUT'],
            'INPUT_FIELDS': [''],
            'OVERLAY': parameters['uykigruntowe'],
            'OVERLAY_FIELDS': [''],
            'OVERLAY_FIELDS_PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['intersection_fplots'] = processing.run('native:intersection', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'id_land_use',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 1,  
            'FORMULA': '$id',
            'INPUT': outputs['intersection_fplots']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['id_land_use'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'INPUT': outputs['id_land_use']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['line_plot'] = processing.run('native:polygonstolines', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'INPUT': outputs['line_plot']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['l_to_line_plot'] = processing.run('native:explodelines', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'ALL_PARTS': False,
            'INPUT': outputs['l_to_line_plot']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['centroid_line_plot'] = processing.run('native:centroids', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'INPUT': outputs['centroid_line_plot']['OUTPUT'],
            'INPUT_FIELDS': [''],
            'OVERLAY': outputs['id_land_use']['OUTPUT'],
            'OVERLAY_FIELDS': [''],
            'OVERLAY_FIELDS_PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['intersection_tplot'] = processing.run('native:intersection', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'FIELD_LENGTH': 1,
            'FIELD_NAME': 'eq_land_use',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 1,  
            'FORMULA': 'CASE \r\nWHEN "uzytki_gru" = \'Ls\' AND ("uzytki_gru_2" = \'Ls\' OR "uzytki_gru_2" = \'Ł\' OR "uzytki_gru_2" = \'P\' OR "uzytki_gru_2" = \'Wi\' OR "uzytki_gru_2" = \'Wrz\' OR "uzytki_gru_2" = \'Tk\' OR "uzytki_gru_2" = \'Tz\' OR "uzytki_gru_2" = \'N\' OR "uzytki_gru_2" = \'Z\') THEN 1 \r\nWHEN "uzytki_gru" = \'Ł\' AND ("uzytki_gru_2" = \'Ls\' OR "uzytki_gru_2" = \'Ł\' OR "uzytki_gru_2" = \'P\' OR "uzytki_gru_2" = \'R\' OR "uzytki_gru_2" = \'Wrz\' OR "uzytki_gru_2" = \'N\' OR "uzytki_gru_2" = \'Z\') THEN 1 \r\nWHEN "uzytki_gru" = \'P\' AND ("uzytki_gru_2" = \'Ls\' OR "uzytki_gru_2" = \'Ł\' OR "uzytki_gru_2" = \'P\' OR "uzytki_gru_2" = \'R\' OR "uzytki_gru_2" = \'N\' OR "uzytki_gru_2" = \'Z\') THEN 1 \r\nWHEN "uzytki_gru" = \'R\' AND ("uzytki_gru_2" = \'Ł\' OR "uzytki_gru_2" = \'P\' OR "uzytki_gru_2" = \'R\') THEN 1 \r\nWHEN "uzytki_gru" = \'Wi\' AND ("uzytki_gru_2" = \'Ls\' OR "uzytki_gru_2" = \'Wi\' OR "uzytki_gru_2" = \'Wrz\' OR "uzytki_gru_2" = \'N\') THEN 1 \r\nWHEN "uzytki_gru" = \'Wrz\' AND ("uzytki_gru_2" = \'Ls\' OR "uzytki_gru_2" = \'Ł\' OR "uzytki_gru_2" = \'Wi\' OR "uzytki_gru_2" = \'Wrz\') THEN 1 \r\nWHEN "uzytki_gru" = \'Tk\' AND ("uzytki_gru_2" = \'Ls\' OR "uzytki_gru_2" = \'Tk\' OR "uzytki_gru_2" = \'Z\') THEN 1 \r\nWHEN "uzytki_gru" = \'Tz\' AND ("uzytki_gru_2" = \'Ls\' OR "uzytki_gru_2" = \'Tz\' OR "uzytki_gru_2" = \'Z\') THEN 1 \r\nWHEN "uzytki_gru" = \'N\' AND ("uzytki_gru_2" = \'Ls\' OR "uzytki_gru_2" = \'Ł\' OR "uzytki_gru_2" = \'P\' OR "uzytki_gru_2" = \'Wi\' OR "uzytki_gru_2" = \'N\' OR "uzytki_gru_2" = \'Z\') THEN 1 \r\nWHEN "uzytki_gru" = \'Z\' AND ("uzytki_gru_2" = \'Ls\' OR "uzytki_gru_2" = \'Ł\' OR "uzytki_gru_2" = \'P\' OR "uzytki_gru_2" = \'Tk\' OR "uzytki_gru_2" = \'Tz\' OR "uzytki_gru_2" = \'N\' OR "uzytki_gru_2" = \'Z\') THEN 1 \r\nWHEN "uzytki_gru" LIKE "uzytki_gru_2" THEN 1\r\nELSE 0 \r\nEND',
            'INPUT': outputs['intersection_tplot']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['eq_land_use'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'AGGREGATES': [{'aggregate': 'first_value','delimiter': ',','input': '"teryt"','length': 50,'name': 'teryt','precision': 0,'type': 10},{'aggregate': 'first_value','delimiter': ',','input': '"id_plots"','length': 10,'name': 'id_plots','precision': 0,'type': 2},{'aggregate': 'minimum','delimiter': ',','input': '"eq_land_use"','length': 1,'name': 'eq_land_use','precision': 0,'type': 2}],
            'GROUP_BY': 'id_plots',
            'INPUT': outputs['eq_land_use']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['agg_plot'] = processing.run('native:aggregate', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}
     
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'FIELD': 'id_plots',
            'FIELDS_TO_COPY': ['eq_land_use'],
            'FIELD_2': 'id_plots',
            'INPUT': outputs['id_plots']['OUTPUT'],
            'INPUT_2': outputs['agg_plot']['OUTPUT'],
            'METHOD': 1,  
            'PREFIX': '',
            'OUTPUT': parameters['Wynik']
        }
        outputs['join_plot'] = processing.run('native:joinattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Wynik'] = outputs['join_plot']['OUTPUT']
        return results

    def name(self):
        return 'HarmonijnoscPrzestrzennaUzytkowania'

    def displayName(self):
        return 'harmonijnosc przestrzenna uzytkowania (tabela 8)'

    def group(self):
        return 'ocena ładu przestrzennego obszarów wiejskich'

    def groupId(self):
        return 'ocena ładu przestrzennego obszarów wiejskich'

    def createInstance(self):
        return HarmonijnoscPrzestrzennaUzytkowania()
