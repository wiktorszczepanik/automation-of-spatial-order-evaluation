from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsExpression
import processing


class KsztaltFigurProcessingAlgorithm(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer('dziakiewidencyjne', 'Działki ewidencyjne', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Ocena', 'ocena', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(47, model_feedback)
        results = {}
        outputs = {}

        # numer_dzialek
        alg_params = {
            'FIELD_LENGTH': 100000,
            'FIELD_NAME': 'numer_dzialek',
            'FIELD_PRECISION': 1,
            'FIELD_TYPE': 1,  # Integer
            'FORMULA': '$id + 1',
            'INPUT': parameters['dziakiewidencyjne'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Numer_dzialek'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # powierzchnia_dzialek
        alg_params = {
            'FIELD_LENGTH': 20,
            'FIELD_NAME': 'powierzchnia_dzialek',
            'FIELD_PRECISION': 2,
            'FIELD_TYPE': 0,  # Float
            'FORMULA': '$area/10000',
            'INPUT': outputs['Numer_dzialek']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Powierzchnia_dzialek'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # bufor_statystyczny
        alg_params = {
            'DISSOLVE': False,
            'DISTANCE': -0.01,
            'END_CAP_STYLE': 1,  # Flat
            'INPUT': outputs['Powierzchnia_dzialek']['OUTPUT'],
            'JOIN_STYLE': 1,  # Miter
            'MITER_LIMIT': 2,
            'SEGMENTS': 5,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Bufor_statystyczny'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # katy_figur
        alg_params = {
            'POLYGONS': outputs['Bufor_statystyczny']['OUTPUT'],
            'ANGLES': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Katy_figur'] = processing.run('lftools:calculatepolygonangles', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # case_angles
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'case_angles',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  # String
            'FORMULA': 'CASE\r\nWHEN "ang_inner_dd" > 85 AND "ang_inner_dd" < 95 THEN \'left\'\r\nELSE \'drop\'\r\nEND',
            'INPUT': outputs['Katy_figur']['ANGLES'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Case_angles'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # poligony_na_linie
        alg_params = {
            'INPUT': outputs['Bufor_statystyczny']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Poligony_na_linie'] = processing.run('native:polygonstolines', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # pozostaw_katy_proste
        alg_params = {
            'FIELD': 'case_angles',
            'INPUT': outputs['Case_angles']['OUTPUT'],
            'OPERATOR': 0,  # =
            'VALUE': 'left',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Pozostaw_katy_proste'] = processing.run('native:extractbyattribute', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # obwod_granic_dzialki
        alg_params = {
            'FIELD_LENGTH': 50,
            'FIELD_NAME': 'obwod_granic_dzialki',
            'FIELD_PRECISION': 1,
            'FIELD_TYPE': 0,  # Float
            'FORMULA': '$length',
            'INPUT': outputs['Poligony_na_linie']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Obwod_granic_dzialki'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # uprosc_linie
        alg_params = {
            'INPUT': outputs['Obwod_granic_dzialki']['OUTPUT'],
            'METHOD': 0,  # Distance (Douglas-Peucker)
            'TOLERANCE': 1,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Uprosc_linie'] = processing.run('native:simplifygeometries', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}

        # wyodrebnij_granice
        alg_params = {
            'INPUT': outputs['Uprosc_linie']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Wyodrebnij_granice'] = processing.run('native:explodelines', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(10)
        if feedback.isCanceled():
            return {}

        # zlacz_granice_w_kierunku
        alg_params = {
            'ANGLE': 10,
            'LINES': outputs['Wyodrebnij_granice']['OUTPUT'],
            'TYPE': 1,  # keep the attributes of the longest line
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Zlacz_granice_w_kierunku'] = processing.run('lftools:directionalmerge', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(11)
        if feedback.isCanceled():
            return {}

        # numery_granic_dzialek
        alg_params = {
            'FIELD_NAME': 'numery_granic_dzialek',
            'GROUP_FIELDS': QgsExpression("'numer_dzialek'").evaluate(),
            'INPUT': outputs['Wyodrebnij_granice']['OUTPUT'],
            'MODULUS': 0,
            'SORT_ASCENDING': True,
            'SORT_EXPRESSION': '',
            'SORT_NULLS_FIRST': False,
            'START': 1,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Numery_granic_dzialek'] = processing.run('native:addautoincrementalfield', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(12)
        if feedback.isCanceled():
            return {}

        # liczba_granic
        alg_params = {
            'FIELD_LENGTH': 100,
            'FIELD_NAME': 'liczba_granic',
            'FIELD_PRECISION': 1,
            'FIELD_TYPE': 1,  # Integer
            'FORMULA': ' count("numer_dzialek", "numer_dzialek")',
            'INPUT': outputs['Numery_granic_dzialek']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Liczba_granic'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(13)
        if feedback.isCanceled():
            return {}

        # numery_granic_dzialek_nieregularne
        alg_params = {
            'FIELD_NAME': 'numery_granic_dzialek_nieregularne',
            'GROUP_FIELDS': QgsExpression("'numer_dzialek'").evaluate(),
            'INPUT': outputs['Zlacz_granice_w_kierunku']['OUTPUT'],
            'MODULUS': 0,
            'SORT_ASCENDING': True,
            'SORT_EXPRESSION': '',
            'SORT_NULLS_FIRST': False,
            'START': 1,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Numery_granic_dzialek_nieregularne'] = processing.run('native:addautoincrementalfield', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(14)
        if feedback.isCanceled():
            return {}

        # dlugosc_granic_nieregularne
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'dlugosc_granic_nieregularne',
            'FIELD_PRECISION': 1,
            'FIELD_TYPE': 0,  # Float
            'FORMULA': '$length',
            'INPUT': outputs['Numery_granic_dzialek_nieregularne']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Dlugosc_granic_nieregularne'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(15)
        if feedback.isCanceled():
            return {}

        # czy_liczba_granic_cztery
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'czy_liczba_granic_cztery',
            'FIELD_PRECISION': 1,
            'FIELD_TYPE': 2,  # String
            'FORMULA': 'CASE\r\nWHEN "liczba_granic" = 4 THEN True\r\nELSE False\r\nEND',
            'INPUT': outputs['Liczba_granic']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Czy_liczba_granic_cztery'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(16)
        if feedback.isCanceled():
            return {}

        # azymut_granic_nieregularne
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'azymut_granic_nieregularne',
            'FIELD_PRECISION': 1,
            'FIELD_TYPE': 0,  # Float
            'FORMULA': 'if(degrees(azimuth(point_n($geometry,1),(end_point($geometry)))) <= 180, degrees(azimuth(point_n($geometry,1),(end_point($geometry)))), degrees(azimuth(point_n($geometry,1),(end_point($geometry)))) - 180)',
            'INPUT': outputs['Dlugosc_granic_nieregularne']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Azymut_granic_nieregularne'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(17)
        if feedback.isCanceled():
            return {}

        # kolejnosc_dlugosc_granic_nieregularne
        alg_params = {
            'FIELD_NAME': 'kolejnosc_dlugosc_granic_nieregularne',
            'GROUP_FIELDS': QgsExpression("'numer_dzialek'").evaluate(),
            'INPUT': outputs['Azymut_granic_nieregularne']['OUTPUT'],
            'MODULUS': 0,
            'SORT_ASCENDING': False,
            'SORT_EXPRESSION': QgsExpression("'dlugosc_granic_nieregularne'").evaluate(),
            'SORT_NULLS_FIRST': False,
            'START': 1,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Kolejnosc_dlugosc_granic_nieregularne'] = processing.run('native:addautoincrementalfield', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(18)
        if feedback.isCanceled():
            return {}

        # dlugosc_granic
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'dlugosc_granic',
            'FIELD_PRECISION': 1,
            'FIELD_TYPE': 0,  # Float
            'FORMULA': '$length',
            'INPUT': outputs['Czy_liczba_granic_cztery']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Dlugosc_granic'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(19)
        if feedback.isCanceled():
            return {}

        # czy_obwod
        alg_params = {
            'FIELD_LENGTH': 50,
            'FIELD_NAME': 'czy_obwod',
            'FIELD_PRECISION': 1,
            'FIELD_TYPE': 2,  # String
            'FORMULA': 'if(range("dlugosc_granic", "numer_dzialek") <= ("obwod_granic_dzialki" * 0.05), True, False)',
            'INPUT': outputs['Dlugosc_granic']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Czy_obwod'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(20)
        if feedback.isCanceled():
            return {}

        # azymut_dluzszych_granic_nieregularne
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'azymut_dluzszych_granic_nieregularne',
            'FIELD_PRECISION': 1,
            'FIELD_TYPE': 0,  # Float
            'FORMULA': 'CASE\r\nWHEN "kolejnosc_dlugosc_granic_nieregularne" = 1 THEN "azymut_granic_nieregularne"\r\nWHEN "kolejnosc_dlugosc_granic_nieregularne" = 2 THEN "azymut_granic_nieregularne"\r\nEND',
            'INPUT': outputs['Kolejnosc_dlugosc_granic_nieregularne']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Azymut_dluzszych_granic_nieregularne'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(21)
        if feedback.isCanceled():
            return {}

        # range_azymut_dluzszych_granic_nieregularne
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'range_azymut_dluzszych_granic_nieregularne',
            'FIELD_PRECISION': 1,
            'FIELD_TYPE': 0,  # Float
            'FORMULA': 'range("azymut_dluzszych_granic_nieregularne", "numer_dzialek")',
            'INPUT': outputs['Azymut_dluzszych_granic_nieregularne']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Range_azymut_dluzszych_granic_nieregularne'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(22)
        if feedback.isCanceled():
            return {}

        # czy_azymut_dlugie_nieregularne
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'czy_azymut_dlugie_nieregularne',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  # String
            'FORMULA': 'CASE\r\nWHEN "range_azymut_dluzszych_granic_nieregularne" <= 2 THEN True\r\nEND',
            'INPUT': outputs['Range_azymut_dluzszych_granic_nieregularne']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Czy_azymut_dlugie_nieregularne'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(23)
        if feedback.isCanceled():
            return {}

        # azymut_granic
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'azymut_granic',
            'FIELD_PRECISION': 1,
            'FIELD_TYPE': 0,  # Float
            'FORMULA': 'if(degrees(azimuth(point_n($geometry,1),(end_point($geometry)))) <= 180, degrees(azimuth(point_n($geometry,1),(end_point($geometry)))), degrees(azimuth(point_n($geometry,1),(end_point($geometry)))) - 180)',
            'INPUT': outputs['Czy_obwod']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Azymut_granic'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(24)
        if feedback.isCanceled():
            return {}

        # liczba_zalaman_nieregularne
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'liczba_zalaman_nieregularne',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 1,  # Integer
            'FORMULA': 'num_points($geometry) - 2',
            'INPUT': outputs['Czy_azymut_dlugie_nieregularne']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Liczba_zalaman_nieregularne'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(25)
        if feedback.isCanceled():
            return {}

        # pary_bokow
        alg_params = {
            'FIELD_LENGTH': 1,
            'FIELD_NAME': 'pary_bokow',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 1,  # Integer
            'FORMULA': 'CASE\r\nWHEN "numery_granic_dzialek" = 1 OR "numery_granic_dzialek" = 3 THEN 1\r\nWHEN "numery_granic_dzialek" = 2 OR "numery_granic_dzialek" = 4 THEN 2\r\nELSE 0\r\nEND',
            'INPUT': outputs['Azymut_granic']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Pary_bokow'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(26)
        if feedback.isCanceled():
            return {}

        # dlugosc_pierwsza_para
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'dlugosc_pierwsza_para',
            'FIELD_PRECISION': 1,
            'FIELD_TYPE': 0,  # Float
            'FORMULA': 'CASE\r\nWHEN "pary_bokow" = 1 THEN "dlugosc_granic"\r\nEND',
            'INPUT': outputs['Pary_bokow']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Dlugosc_pierwsza_para'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(27)
        if feedback.isCanceled():
            return {}

        # zalamania_na_dlugiej_nieregularne
        alg_params = {
            'FIELD_LENGTH': 5,
            'FIELD_NAME': 'zalamania_na_dlugiej_nieregularne',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 1,  # Integer
            'FORMULA': 'CASE\r\nWHEN "kolejnosc_dlugosc_granic_nieregularne" = 1 THEN "liczba_zalaman_nieregularne"\r\nWHEN "kolejnosc_dlugosc_granic_nieregularne" = 2 THEN "liczba_zalaman_nieregularne"\r\nELSE 0\r\nEND',
            'INPUT': outputs['Liczba_zalaman_nieregularne']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Zalamania_na_dlugiej_nieregularne'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(28)
        if feedback.isCanceled():
            return {}

        # dlugosc_druga_para
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'dlugosc_druga_para',
            'FIELD_PRECISION': 1,
            'FIELD_TYPE': 0,  # Float
            'FORMULA': 'CASE\r\nWHEN "pary_bokow" = 2 THEN "dlugosc_granic"\r\nEND',
            'INPUT': outputs['Dlugosc_pierwsza_para']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Dlugosc_druga_para'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(29)
        if feedback.isCanceled():
            return {}

        # agreguj_wstepne_wyniki_nieregularne
        alg_params = {
            'AGGREGATES': [{'aggregate': 'first_value','delimiter': ',','input': '"teryt"','length': 254,'name': 'teryt','precision': 0,'type': 10},{'aggregate': 'first_value','delimiter': ',','input': '"numer_dzialek"','length': 10,'name': 'numer_dzialek','precision': 0,'type': 2},{'aggregate': 'first_value','delimiter': ',','input': '"czy_azymut_dlugie_nieregularne"','length': 10,'name': 'czy_azymut_dlugie_nieregularne','precision': 0,'type': 1},{'aggregate': 'sum','delimiter': ',','input': '"zalamania_na_dlugiej_nieregularne"','length': 10,'name': 'zalamania_na_dlugiej_nieregularne','precision': 0,'type': 2}],
            'GROUP_BY': 'numer_dzialek',
            'INPUT': outputs['Zalamania_na_dlugiej_nieregularne']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Agreguj_wstepne_wyniki_nieregularne'] = processing.run('native:aggregate', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(30)
        if feedback.isCanceled():
            return {}

        # range_dlugosc_pierwsza_para
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'range_dlugosc_pierwsza_para',
            'FIELD_PRECISION': 1,
            'FIELD_TYPE': 0,  # Float
            'FORMULA': 'range("dlugosc_pierwsza_para", "numer_dzialek")',
            'INPUT': outputs['Dlugosc_druga_para']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Range_dlugosc_pierwsza_para'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(31)
        if feedback.isCanceled():
            return {}

        # range_dlugosc_druga_para
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'range_dlugosc_druga_para',
            'FIELD_PRECISION': 1,
            'FIELD_TYPE': 0,  # Float
            'FORMULA': 'range("dlugosc_druga_para", "numer_dzialek")',
            'INPUT': outputs['Range_dlugosc_pierwsza_para']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Range_dlugosc_druga_para'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(32)
        if feedback.isCanceled():
            return {}

        # czy_dlugosc_pierwsza_para
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'czy_dlugosc_pierwsza_para',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  # String
            'FORMULA': 'CASE\r\nWHEN "range_dlugosc_pierwsza_para" <= ("obwod_granic_dzialki" * 0.01) THEN True\r\nEND',
            'INPUT': outputs['Range_dlugosc_druga_para']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Czy_dlugosc_pierwsza_para'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(33)
        if feedback.isCanceled():
            return {}

        # czy_dlugosc_druga_para
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'czy_dlugosc_druga_para',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  # String
            'FORMULA': 'CASE\r\nWHEN "range_dlugosc_druga_para" <= ("obwod_granic_dzialki" * 0.01) THEN True\r\nEND',
            'INPUT': outputs['Czy_dlugosc_pierwsza_para']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Czy_dlugosc_druga_para'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(34)
        if feedback.isCanceled():
            return {}

        # azymut_pierwsza_para
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'azymut_pierwsza_para',
            'FIELD_PRECISION': 1,
            'FIELD_TYPE': 0,  # Float
            'FORMULA': 'CASE\r\nWHEN "pary_bokow" = 1 THEN "azymut_granic"\r\nEND',
            'INPUT': outputs['Czy_dlugosc_druga_para']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Azymut_pierwsza_para'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(35)
        if feedback.isCanceled():
            return {}

        # azymut_druga_para
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'azymut_druga_para',
            'FIELD_PRECISION': 1,
            'FIELD_TYPE': 0,  # Float
            'FORMULA': 'CASE\r\nWHEN "pary_bokow" = 2 THEN "azymut_granic"\r\nEND',
            'INPUT': outputs['Azymut_pierwsza_para']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Azymut_druga_para'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(36)
        if feedback.isCanceled():
            return {}

        # range_azymut_pierwsza_para
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'range_azymut_pierwsza_para',
            'FIELD_PRECISION': 1,
            'FIELD_TYPE': 0,  # Float
            'FORMULA': 'range("azymut_pierwsza_para", "numer_dzialek")',
            'INPUT': outputs['Azymut_druga_para']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Range_azymut_pierwsza_para'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(37)
        if feedback.isCanceled():
            return {}

        # range_azymut_druga_para
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'range_azymut_druga_para',
            'FIELD_PRECISION': 1,
            'FIELD_TYPE': 0,  # Float
            'FORMULA': 'range("azymut_druga_para", "numer_dzialek")',
            'INPUT': outputs['Range_azymut_pierwsza_para']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Range_azymut_druga_para'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(38)
        if feedback.isCanceled():
            return {}

        # czy_azymut_pierwsza_para
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'czy_azymut_pierwsza_para',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  # String
            'FORMULA': 'CASE\r\nWHEN "range_azymut_pierwsza_para" <= 2 THEN True\r\nEND',
            'INPUT': outputs['Range_azymut_druga_para']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Czy_azymut_pierwsza_para'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(39)
        if feedback.isCanceled():
            return {}

        # czy_azymut_druga_para
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'czy_azymut_druga_para',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  # String
            'FORMULA': 'CASE\r\nWHEN "range_azymut_druga_para" <= 2 THEN True\r\nEND',
            'INPUT': outputs['Czy_azymut_pierwsza_para']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Czy_azymut_druga_para'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(40)
        if feedback.isCanceled():
            return {}

        # agreguj_wstepne_wyniki_regularne
        alg_params = {
            'AGGREGATES': [{'aggregate': 'first_value','delimiter': ',','input': '"teryt"','length': 254,'name': 'teryt','precision': 0,'type': 10},{'aggregate': 'first_value','delimiter': ',','input': '"numer_dzialek"','length': 10,'name': 'numer_dzialek','precision': 0,'type': 2},{'aggregate': 'first_value','delimiter': ',','input': '"powierzchnia_dzialek"','length': 20,'name': 'powierzchnia_dzialek','precision': 2,'type': 6},{'aggregate': 'first_value','delimiter': ',','input': '"czy_obwod"','length': 10,'name': 'czy_obwod','precision': 0,'type': 1},{'aggregate': 'first_value','delimiter': ',','input': '"czy_dlugosc_pierwsza_para"','length': 10,'name': 'czy_dlugosc_pierwsza_para','precision': 0,'type': 1},{'aggregate': 'first_value','delimiter': ',','input': '"czy_dlugosc_druga_para"','length': 10,'name': 'czy_dlugosc_druga_para','precision': 0,'type': 1},{'aggregate': 'first_value','delimiter': ',','input': '"czy_azymut_pierwsza_para"','length': 10,'name': 'czy_azymut_pierwsza_para','precision': 0,'type': 1},{'aggregate': 'first_value','delimiter': ',','input': '"czy_azymut_druga_para"','length': 10,'name': 'czy_azymut_druga_para','precision': 0,'type': 1},{'aggregate': 'first_value','delimiter': ',','input': '"czy_liczba_granic_cztery"','length': 10,'name': 'czy_liczba_granic_cztery','precision': 0,'type': 1},{'aggregate': 'sum','delimiter': ',','input': '"dlugosc_pierwsza_para"','length': 10,'name': 'dlugosc_pierwsza_para','precision': 2,'type': 6},{'aggregate': 'sum','delimiter': ',','input': '"dlugosc_druga_para"','length': 10,'name': 'dlugosc_druga_para','precision': 2,'type': 6}],
            'GROUP_BY': 'numer_dzialek',
            'INPUT': outputs['Czy_azymut_druga_para']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Agreguj_wstepne_wyniki_regularne'] = processing.run('native:aggregate', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(41)
        if feedback.isCanceled():
            return {}

        # ktora_dluzsza_para
        alg_params = {
            'FIELD_LENGTH': 2,
            'FIELD_NAME': 'ktora_dluzsza_para',
            'FIELD_PRECISION': 1,
            'FIELD_TYPE': 1,  # Integer
            'FORMULA': 'CASE\r\nWHEN "dlugosc_pierwsza_para" > "dlugosc_druga_para" THEN 1\r\nWHEN "dlugosc_pierwsza_para" < "dlugosc_druga_para" THEN 2\r\nELSE 0\r\nEND\r\n',
            'INPUT': outputs['Agreguj_wstepne_wyniki_regularne']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Ktora_dluzsza_para'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(42)
        if feedback.isCanceled():
            return {}

        # laczenie_dzialki_regularne
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'FIELD': 'numer_dzialek',
            'FIELDS_TO_COPY': ['powierzchnia_dzialek','czy_obwod','czy_dlugosc_pierwsza_para','czy_dlugosc_druga_para','czy_azymut_pierwsza_para','czy_azymut_druga_para','czy_liczba_granic_cztery','ktora_dluzsza_para'],
            'FIELD_2': 'numer_dzialek',
            'INPUT': outputs['Numer_dzialek']['OUTPUT'],
            'INPUT_2': outputs['Ktora_dluzsza_para']['OUTPUT'],
            'METHOD': 1,  # Take attributes of the first matching feature only (one-to-one)
            'PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Laczenie_dzialki_regularne'] = processing.run('native:joinattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(43)
        if feedback.isCanceled():
            return {}

        # liczba_katow_prostych
        alg_params = {
            'CLASSFIELD': '',
            'FIELD': 'liczba_katow_prostych',
            'POINTS': outputs['Pozostaw_katy_proste']['OUTPUT'],
            'POLYGONS': outputs['Laczenie_dzialki_regularne']['OUTPUT'],
            'WEIGHT': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Liczba_katow_prostych'] = processing.run('native:countpointsinpolygon', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(44)
        if feedback.isCanceled():
            return {}

        # laczenie_dzialki_wszystkie
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'FIELD': 'numer_dzialek',
            'FIELDS_TO_COPY': ['czy_azymut_dlugie_nieregularne','zalamania_na_dlugiej_nieregularne'],
            'FIELD_2': 'numer_dzialek',
            'INPUT': outputs['Liczba_katow_prostych']['OUTPUT'],
            'INPUT_2': outputs['Agreguj_wstepne_wyniki_nieregularne']['OUTPUT'],
            'METHOD': 1,  # Take attributes of the first matching feature only (one-to-one)
            'PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Laczenie_dzialki_wszystkie'] = processing.run('native:joinattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(45)
        if feedback.isCanceled():
            return {}

        # oceny_ksztaltu
        alg_params = {
            'FIELD_LENGTH': 1,
            'FIELD_NAME': 'oceny_ksztaltu',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 1,  # Integer
            'FORMULA': 'CASE\r\nWHEN "powierzchnia_dzialek" >= 0 AND "powierzchnia_dzialek" <= 1 AND "czy_obwod" = TRUE AND "czy_dlugosc_pierwsza_para" = TRUE AND "czy_dlugosc_druga_para" = TRUE AND "czy_azymut_pierwsza_para" = TRUE AND "czy_azymut_druga_para" = TRUE AND "czy_liczba_granic_cztery" = TRUE AND "liczba_katow_prostych" = 4 THEN 2\r\nWHEN "powierzchnia_dzialek" > 1 AND "powierzchnia_dzialek" <= 2 AND "czy_dlugosc_pierwsza_para" = TRUE AND "czy_dlugosc_druga_para" = TRUE AND "czy_azymut_pierwsza_para" = TRUE AND "czy_azymut_druga_para" = TRUE AND "czy_liczba_granic_cztery" = TRUE AND "liczba_katow_prostych" = 4 THEN 2\r\nWHEN "powierzchnia_dzialek" > 2 AND "powierzchnia_dzialek" <= 5 AND "czy_azymut_pierwsza_para" = TRUE AND "czy_azymut_druga_para" = TRUE AND "czy_liczba_granic_cztery" = TRUE THEN 2\r\nWHEN "powierzchnia_dzialek" > 5 AND "powierzchnia_dzialek" <= 10 AND "czy_liczba_granic_cztery" = TRUE AND "czy_azymut_dlugie_nieregularne" = TRUE THEN 2\r\nWHEN "powierzchnia_dzialek" > 10 AND "czy_liczba_granic_cztery" = TRUE THEN 2\r\nWHEN "powierzchnia_dzialek" >= 0 AND "powierzchnia_dzialek" <= 1 AND "czy_azymut_dlugie_nieregularne" = TRUE THEN 1\r\nWHEN "powierzchnia_dzialek" > 1 AND "powierzchnia_dzialek" <= 2 AND "czy_azymut_dlugie_nieregularne" = TRUE AND "zalamania_na_dlugiej_nieregularne" <= 1 THEN 1\r\nWHEN "powierzchnia_dzialek" > 2 AND "powierzchnia_dzialek" <= 5 AND "czy_azymut_dlugie_nieregularne" = TRUE AND "zalamania_na_dlugiej_nieregularne" <= 2 THEN 1 \r\nWHEN "powierzchnia_dzialek" > 5 AND "powierzchnia_dzialek" <= 10 AND "czy_azymut_dlugie_nieregularne" = TRUE AND "zalamania_na_dlugiej_nieregularne" <= 3 THEN 1 \r\nWHEN "powierzchnia_dzialek" > 10 AND "czy_azymut_dlugie_nieregularne" = TRUE THEN 1\r\nELSE 0\r\nEND',
            'INPUT': outputs['Laczenie_dzialki_wszystkie']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Oceny_ksztaltu'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(46)
        if feedback.isCanceled():
            return {}

        # usun_kolumny
        alg_params = {
            'COLUMN': ['numer_dzialek','powierzchnia_dzialek','czy_obwod','czy_dlugosc_pierwsza_para','czy_dlugosc_druga_para','czy_azymut_pierwsza_para','czy_azymut_druga_para','czy_liczba_granic_cztery','ktora_dluzsza_para','liczba_katow_prostych','czy_azymut_dlugie_nieregularne','zalamania_na_dlugiej_nieregularne'],
            'INPUT': outputs['Oceny_ksztaltu']['OUTPUT'],
            'OUTPUT': parameters['Ocena']
        }
        outputs['Usun_kolumny'] = processing.run('native:deletecolumn', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Ocena'] = outputs['Usun_kolumny']['OUTPUT']
        return results

    def name(self):
        return 'KsztaltFigurProcessingAlgorithm'

    def displayName(self):
        return 'kształt figur (tabela 1)'

    def group(self):
        return 'ocena ładu przestrzennego obszarów wiejskich'

    def groupId(self):
        return 'ocena ładu przestrzennego obszarów wiejskich'

    def createInstance(self):
        return KsztaltFigurProcessingAlgorithm()
