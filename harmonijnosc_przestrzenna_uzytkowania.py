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
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(10, model_feedback)
        results = {}
        outputs = {}

        # dzialki_id
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'dzialki_id',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 1,  # Integer
            'FORMULA': '$id',
            'INPUT': parameters['dziakiewidencyjne'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Dzialki_id'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # przeciecie_jeden
        alg_params = {
            'INPUT': outputs['Dzialki_id']['OUTPUT'],
            'INPUT_FIELDS': [''],
            'OVERLAY': parameters['uykigruntowe'],
            'OVERLAY_FIELDS': [''],
            'OVERLAY_FIELDS_PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Przeciecie_jeden'] = processing.run('native:intersection', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # uzytek_id
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'uzytek_id',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 1,  # Integer
            'FORMULA': '$id',
            'INPUT': outputs['Przeciecie_jeden']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Uzytek_id'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # poligony_na_linie
        alg_params = {
            'INPUT': outputs['Uzytek_id']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Poligony_na_linie'] = processing.run('native:polygonstolines', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # linia_na_linie
        alg_params = {
            'INPUT': outputs['Poligony_na_linie']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Linia_na_linie'] = processing.run('native:explodelines', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # centroidy_dla_kazdej_linii
        alg_params = {
            'ALL_PARTS': False,
            'INPUT': outputs['Linia_na_linie']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Centroidy_dla_kazdej_linii'] = processing.run('native:centroids', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # przeciecie_dwa
        alg_params = {
            'INPUT': outputs['Centroidy_dla_kazdej_linii']['OUTPUT'],
            'INPUT_FIELDS': [''],
            'OVERLAY': outputs['Uzytek_id']['OUTPUT'],
            'OVERLAY_FIELDS': [''],
            'OVERLAY_FIELDS_PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Przeciecie_dwa'] = processing.run('native:intersection', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # czy_pasuja_uzytki
        alg_params = {
            'FIELD_LENGTH': 1,
            'FIELD_NAME': 'czy_pasuja_uzytki',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 1,  # Integer
            'FORMULA': 'CASE \r\nWHEN "uzytki_gru" = \'Ls\' AND ("uzytki_gru_2" = \'Ls\' OR "uzytki_gru_2" = \'Ł\' OR "uzytki_gru_2" = \'P\' OR "uzytki_gru_2" = \'Wi\' OR "uzytki_gru_2" = \'Wrz\' OR "uzytki_gru_2" = \'Tk\' OR "uzytki_gru_2" = \'Tz\' OR "uzytki_gru_2" = \'N\' OR "uzytki_gru_2" = \'Z\') THEN 1 \r\nWHEN "uzytki_gru" = \'Ł\' AND ("uzytki_gru_2" = \'Ls\' OR "uzytki_gru_2" = \'Ł\' OR "uzytki_gru_2" = \'P\' OR "uzytki_gru_2" = \'R\' OR "uzytki_gru_2" = \'Wrz\' OR "uzytki_gru_2" = \'N\' OR "uzytki_gru_2" = \'Z\') THEN 1 \r\nWHEN "uzytki_gru" = \'P\' AND ("uzytki_gru_2" = \'Ls\' OR "uzytki_gru_2" = \'Ł\' OR "uzytki_gru_2" = \'P\' OR "uzytki_gru_2" = \'R\' OR "uzytki_gru_2" = \'N\' OR "uzytki_gru_2" = \'Z\') THEN 1 \r\nWHEN "uzytki_gru" = \'R\' AND ("uzytki_gru_2" = \'Ł\' OR "uzytki_gru_2" = \'P\' OR "uzytki_gru_2" = \'R\') THEN 1 \r\nWHEN "uzytki_gru" = \'Wi\' AND ("uzytki_gru_2" = \'Ls\' OR "uzytki_gru_2" = \'Wi\' OR "uzytki_gru_2" = \'Wrz\' OR "uzytki_gru_2" = \'N\') THEN 1 \r\nWHEN "uzytki_gru" = \'Wrz\' AND ("uzytki_gru_2" = \'Ls\' OR "uzytki_gru_2" = \'Ł\' OR "uzytki_gru_2" = \'Wi\' OR "uzytki_gru_2" = \'Wrz\') THEN 1 \r\nWHEN "uzytki_gru" = \'Tk\' AND ("uzytki_gru_2" = \'Ls\' OR "uzytki_gru_2" = \'Tk\' OR "uzytki_gru_2" = \'Z\') THEN 1 \r\nWHEN "uzytki_gru" = \'Tz\' AND ("uzytki_gru_2" = \'Ls\' OR "uzytki_gru_2" = \'Tz\' OR "uzytki_gru_2" = \'Z\') THEN 1 \r\nWHEN "uzytki_gru" = \'N\' AND ("uzytki_gru_2" = \'Ls\' OR "uzytki_gru_2" = \'Ł\' OR "uzytki_gru_2" = \'P\' OR "uzytki_gru_2" = \'Wi\' OR "uzytki_gru_2" = \'N\' OR "uzytki_gru_2" = \'Z\') THEN 1 \r\nWHEN "uzytki_gru" = \'Z\' AND ("uzytki_gru_2" = \'Ls\' OR "uzytki_gru_2" = \'Ł\' OR "uzytki_gru_2" = \'P\' OR "uzytki_gru_2" = \'Tk\' OR "uzytki_gru_2" = \'Tz\' OR "uzytki_gru_2" = \'N\' OR "uzytki_gru_2" = \'Z\') THEN 1 \r\nWHEN "uzytki_gru" LIKE "uzytki_gru_2" THEN 1\r\nELSE 0 \r\nEND',
            'INPUT': outputs['Przeciecie_dwa']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Czy_pasuja_uzytki'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # agregacja
        alg_params = {
            'AGGREGATES': [{'aggregate': 'first_value','delimiter': ',','input': '"teryt"','length': 50,'name': 'teryt','precision': 0,'type': 10},{'aggregate': 'first_value','delimiter': ',','input': '"dzialki_id"','length': 10,'name': 'dzialki_id','precision': 0,'type': 2},{'aggregate': 'minimum','delimiter': ',','input': '"czy_pasuja_uzytki"','length': 1,'name': 'czy_pasuja_uzytki','precision': 0,'type': 2}],
            'GROUP_BY': 'dzialki_id',
            'INPUT': outputs['Czy_pasuja_uzytki']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Agregacja'] = processing.run('native:aggregate', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}

        # laczenie
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'FIELD': 'dzialki_id',
            'FIELDS_TO_COPY': ['czy_pasuja_uzytki'],
            'FIELD_2': 'dzialki_id',
            'INPUT': outputs['Dzialki_id']['OUTPUT'],
            'INPUT_2': outputs['Agregacja']['OUTPUT'],
            'METHOD': 1,  # Take attributes of the first matching feature only (one-to-one)
            'PREFIX': '',
            'OUTPUT': parameters['Wynik']
        }
        outputs['Laczenie'] = processing.run('native:joinattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Wynik'] = outputs['Laczenie']['OUTPUT']
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
