# -*- coding: utf-8 -*-

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
        feedback = QgsProcessingMultiStepFeedback(47, model_feedback)
        results = {}
        outputs = {}

        alg_params = {
            'FIELD_LENGTH': 100000,
            'FIELD_NAME': 'plot_number',
            'FIELD_PRECISION': 1,
            'FIELD_TYPE': 1,  
            'FORMULA': '$id + 1',
            'INPUT': parameters['dziakiewidencyjne'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['plot_number'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'FIELD_LENGTH': 20,
            'FIELD_NAME': 'area_plot',
            'FIELD_PRECISION': 2,
            'FIELD_TYPE': 0,  
            'FORMULA': '$area/10000',
            'INPUT': outputs['plot_number']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['area_plot'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'DISSOLVE': False,
            'DISTANCE': -0.01,
            'END_CAP_STYLE': 1,  
            'INPUT': outputs['area_plot']['OUTPUT'],
            'JOIN_STYLE': 1,  
            'MITER_LIMIT': 2,
            'SEGMENTS': 5,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['buffer_stat'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'POLYGONS': outputs['buffer_stat']['OUTPUT'],
            'ANGLES': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['angle_plot'] = processing.run('lftools:calculatepolygonangles', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'case_angles',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  
            'FORMULA': 'CASE\r\nWHEN "ang_inner_dd" > 85 AND "ang_inner_dd" < 95 THEN \'left\'\r\nELSE \'drop\'\r\nEND',
            'INPUT': outputs['angle_plot']['ANGLES'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['case_angles'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'INPUT': outputs['buffer_stat']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['line_plot'] = processing.run('native:polygonstolines', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'FIELD': 'case_angles',
            'INPUT': outputs['case_angles']['OUTPUT'],
            'OPERATOR': 0,  # =
            'VALUE': 'left',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['right_angle_plot'] = processing.run('native:extractbyattribute', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'FIELD_LENGTH': 50,
            'FIELD_NAME': 'circuit_plot',
            'FIELD_PRECISION': 1,
            'FIELD_TYPE': 0,  
            'FORMULA': '$length',
            'INPUT': outputs['line_plot']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['circuit_plot'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'INPUT': outputs['circuit_plot']['OUTPUT'],
            'METHOD': 0,  # Distance (Douglas-Peucker)
            'TOLERANCE': 1,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['simplify_line_plot'] = processing.run('native:simplifygeometries', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'INPUT': outputs['simplify_line_plot']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['border_line_plot'] = processing.run('native:explodelines', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(10)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'ANGLE': 10,
            'LINES': outputs['border_line_plot']['OUTPUT'],
            'TYPE': 1,  
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['line_direction_plot'] = processing.run('lftools:directionalmerge', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(11)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'FIELD_NAME': 'number_border_plot',
            'GROUP_FIELDS': QgsExpression("'plot_number'").evaluate(),
            'INPUT': outputs['border_line_plot']['OUTPUT'],
            'MODULUS': 0,
            'SORT_ASCENDING': True,
            'SORT_EXPRESSION': '',
            'SORT_NULLS_FIRST': False,
            'START': 1,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['number_border_plot'] = processing.run('native:addautoincrementalfield', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(12)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'FIELD_LENGTH': 100,
            'FIELD_NAME': 'border_count_plot',
            'FIELD_PRECISION': 1,
            'FIELD_TYPE': 1,  
            'FORMULA': ' count("plot_number", "plot_number")',
            'INPUT': outputs['number_border_plot']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['border_count_plot'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(13)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'FIELD_NAME': 'number_border_plot_unregular',
            'GROUP_FIELDS': QgsExpression("'plot_number'").evaluate(),
            'INPUT': outputs['line_direction_plot']['OUTPUT'],
            'MODULUS': 0,
            'SORT_ASCENDING': True,
            'SORT_EXPRESSION': '',
            'SORT_NULLS_FIRST': False,
            'START': 1,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['number_border_plot_unregular'] = processing.run('native:addautoincrementalfield', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(14)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'border_length_unregular',
            'FIELD_PRECISION': 1,
            'FIELD_TYPE': 0,  
            'FORMULA': '$length',
            'INPUT': outputs['number_border_plot_unregular']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['border_length_unregular'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(15)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'case_border_count_plot',
            'FIELD_PRECISION': 1,
            'FIELD_TYPE': 2,  
            'FORMULA': 'CASE\r\nWHEN "border_count_plot" = 4 THEN True\r\nELSE False\r\nEND',
            'INPUT': outputs['border_count_plot']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['case_border_count_plot'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(16)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'azimuth_border_unregular',
            'FIELD_PRECISION': 1,
            'FIELD_TYPE': 0,  
            'FORMULA': 'if(degrees(azimuth(point_n($geometry,1),(end_point($geometry)))) <= 180, degrees(azimuth(point_n($geometry,1),(end_point($geometry)))), degrees(azimuth(point_n($geometry,1),(end_point($geometry)))) - 180)',
            'INPUT': outputs['border_length_unregular']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['azimuth_border_unregular'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(17)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'FIELD_NAME': 'increment_border_length_unregular_plot',
            'GROUP_FIELDS': QgsExpression("'plot_number'").evaluate(),
            'INPUT': outputs['azimuth_border_unregular']['OUTPUT'],
            'MODULUS': 0,
            'SORT_ASCENDING': False,
            'SORT_EXPRESSION': QgsExpression("'border_length_unregular'").evaluate(),
            'SORT_NULLS_FIRST': False,
            'START': 1,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['increment_border_length_unregular_plot'] = processing.run('native:addautoincrementalfield', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(18)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'sec_length_border_plot',
            'FIELD_PRECISION': 1,
            'FIELD_TYPE': 0,  
            'FORMULA': '$length',
            'INPUT': outputs['case_border_count_plot']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['sec_length_border_plot'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(19)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'FIELD_LENGTH': 50,
            'FIELD_NAME': 'case_border_form',
            'FIELD_PRECISION': 1,
            'FIELD_TYPE': 2,  
            'FORMULA': 'if(range("sec_length_border_plot", "plot_number") <= ("circuit_plot" * 0.05), True, False)',
            'INPUT': outputs['sec_length_border_plot']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['case_border_form'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(20)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'azimuth_longer_border_unregular',
            'FIELD_PRECISION': 1,
            'FIELD_TYPE': 0,  
            'FORMULA': 'CASE\r\nWHEN "increment_border_length_unregular_plot" = 1 THEN "azimuth_border_unregular"\r\nWHEN "increment_border_length_unregular_plot" = 2 THEN "azimuth_border_unregular"\r\nEND',
            'INPUT': outputs['increment_border_length_unregular_plot']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['azimuth_longer_border_unregular'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(21)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'range_azimuth_longer_border_unregular',
            'FIELD_PRECISION': 1,
            'FIELD_TYPE': 0,  
            'FORMULA': 'range("azimuth_longer_border_unregular", "plot_number")',
            'INPUT': outputs['azimuth_longer_border_unregular']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['range_azimuth_longer_border_unregular'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(22)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'case_azimuth_long_unrglr',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  
            'FORMULA': 'CASE\r\nWHEN "range_azimuth_longer_border_unregular" <= 2 THEN True\r\nEND',
            'INPUT': outputs['range_azimuth_longer_border_unregular']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['case_azimuth_long_unrglr'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(23)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'azimuth_border_range_plot',
            'FIELD_PRECISION': 1,
            'FIELD_TYPE': 0,  
            'FORMULA': 'if(degrees(azimuth(point_n($geometry,1),(end_point($geometry)))) <= 180, degrees(azimuth(point_n($geometry,1),(end_point($geometry)))), degrees(azimuth(point_n($geometry,1),(end_point($geometry)))) - 180)',
            'INPUT': outputs['case_border_form']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['azimuth_border_range_plot'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(24)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'count_line_break_unrglr',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 1,  
            'FORMULA': 'num_points($geometry) - 2',
            'INPUT': outputs['case_azimuth_long_unrglr']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['count_line_break_unrglr'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(25)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'FIELD_LENGTH': 1,
            'FIELD_NAME': 'line_pairs_plot',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 1,  
            'FORMULA': 'CASE\r\nWHEN "number_border_plot" = 1 OR "number_border_plot" = 3 THEN 1\r\nWHEN "number_border_plot" = 2 OR "number_border_plot" = 4 THEN 2\r\nELSE 0\r\nEND',
            'INPUT': outputs['azimuth_border_range_plot']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['line_pairs_plot'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(26)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'length_first_pair',
            'FIELD_PRECISION': 1,
            'FIELD_TYPE': 0,  
            'FORMULA': 'CASE\r\nWHEN "line_pairs_plot" = 1 THEN "sec_length_border_plot"\r\nEND',
            'INPUT': outputs['line_pairs_plot']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['length_first_pair'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(27)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'FIELD_LENGTH': 5,
            'FIELD_NAME': 'length_break_first_pair',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 1,  
            'FORMULA': 'CASE\r\nWHEN "increment_border_length_unregular_plot" = 1 THEN "count_line_break_unrglr"\r\nWHEN "increment_border_length_unregular_plot" = 2 THEN "count_line_break_unrglr"\r\nELSE 0\r\nEND',
            'INPUT': outputs['count_line_break_unrglr']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['length_break_first_pair'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(28)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'length_secound_pair',
            'FIELD_PRECISION': 1,
            'FIELD_TYPE': 0,  
            'FORMULA': 'CASE\r\nWHEN "line_pairs_plot" = 2 THEN "sec_length_border_plot"\r\nEND',
            'INPUT': outputs['length_first_pair']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['length_secound_pair'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(29)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'AGGREGATES': [{'aggregate': 'first_value','delimiter': ',','input': '"teryt"','length': 254,'name': 'teryt','precision': 0,'type': 10},{'aggregate': 'first_value','delimiter': ',','input': '"plot_number"','length': 10,'name': 'plot_number','precision': 0,'type': 2},{'aggregate': 'first_value','delimiter': ',','input': '"case_azimuth_long_unrglr"','length': 10,'name': 'case_azimuth_long_unrglr','precision': 0,'type': 1},{'aggregate': 'sum','delimiter': ',','input': '"length_break_first_pair"','length': 10,'name': 'length_break_first_pair','precision': 0,'type': 2}],
            'GROUP_BY': 'plot_number',
            'INPUT': outputs['length_break_first_pair']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['agg_preinput_eq_unregular'] = processing.run('native:aggregate', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(30)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'range_length_first_pair',
            'FIELD_PRECISION': 1,
            'FIELD_TYPE': 0,  
            'FORMULA': 'range("length_first_pair", "plot_number")',
            'INPUT': outputs['length_secound_pair']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['range_length_first_pair'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(31)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'range_length_secound_pair',
            'FIELD_PRECISION': 1,
            'FIELD_TYPE': 0,  
            'FORMULA': 'range("length_secound_pair", "plot_number")',
            'INPUT': outputs['range_length_first_pair']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['range_length_secound_pair'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(32)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'case_length_first_pair_plot',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  
            'FORMULA': 'CASE\r\nWHEN "range_length_first_pair" <= ("circuit_plot" * 0.01) THEN True\r\nEND',
            'INPUT': outputs['range_length_secound_pair']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['case_length_first_pair_plot'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(33)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'case_length_secound_pair_plot',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  
            'FORMULA': 'CASE\r\nWHEN "range_length_secound_pair" <= ("circuit_plot" * 0.01) THEN True\r\nEND',
            'INPUT': outputs['case_length_first_pair_plot']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['case_length_secound_pair_plot'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(34)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'fazimuth_first_pair_plot',
            'FIELD_PRECISION': 1,
            'FIELD_TYPE': 0,  
            'FORMULA': 'CASE\r\nWHEN "line_pairs_plot" = 1 THEN "azimuth_border_range_plot"\r\nEND',
            'INPUT': outputs['case_length_secound_pair_plot']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['fazimuth_first_pair_plot'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(35)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'sazimuth_secound_pair_plot',
            'FIELD_PRECISION': 1,
            'FIELD_TYPE': 0,  
            'FORMULA': 'CASE\r\nWHEN "line_pairs_plot" = 2 THEN "azimuth_border_range_plot"\r\nEND',
            'INPUT': outputs['fazimuth_first_pair_plot']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['sazimuth_secound_pair_plot'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(36)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'range_fazimuth_first_pair_plot',
            'FIELD_PRECISION': 1,
            'FIELD_TYPE': 0,  
            'FORMULA': 'range("fazimuth_first_pair_plot", "plot_number")',
            'INPUT': outputs['sazimuth_secound_pair_plot']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['range_fazimuth_first_pair_plot'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(37)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'range_sazimuth_secound_pair_plot',
            'FIELD_PRECISION': 1,
            'FIELD_TYPE': 0,  
            'FORMULA': 'range("sazimuth_secound_pair_plot", "plot_number")',
            'INPUT': outputs['range_fazimuth_first_pair_plot']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['range_sazimuth_secound_pair_plot'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(38)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'fcase_fazimuth_first_fpair_fplot',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  
            'FORMULA': 'CASE\r\nWHEN "range_fazimuth_first_pair_plot" <= 2 THEN True\r\nEND',
            'INPUT': outputs['range_sazimuth_secound_pair_plot']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['fcase_fazimuth_first_fpair_fplot'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(39)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'scase_sazimuth_secound_spair_splot',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  
            'FORMULA': 'CASE\r\nWHEN "range_sazimuth_secound_pair_plot" <= 2 THEN True\r\nEND',
            'INPUT': outputs['fcase_fazimuth_first_fpair_fplot']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['scase_sazimuth_secound_spair_splot'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(40)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'AGGREGATES': [{'aggregate': 'first_value','delimiter': ',','input': '"teryt"','length': 254,'name': 'teryt','precision': 0,'type': 10},{'aggregate': 'first_value','delimiter': ',','input': '"plot_number"','length': 10,'name': 'plot_number','precision': 0,'type': 2},{'aggregate': 'first_value','delimiter': ',','input': '"area_plot"','length': 20,'name': 'area_plot','precision': 2,'type': 6},{'aggregate': 'first_value','delimiter': ',','input': '"case_border_form"','length': 10,'name': 'case_border_form','precision': 0,'type': 1},{'aggregate': 'first_value','delimiter': ',','input': '"case_length_first_pair_plot"','length': 10,'name': 'case_length_first_pair_plot','precision': 0,'type': 1},{'aggregate': 'first_value','delimiter': ',','input': '"case_length_secound_pair_plot"','length': 10,'name': 'case_length_secound_pair_plot','precision': 0,'type': 1},{'aggregate': 'first_value','delimiter': ',','input': '"fcase_fazimuth_first_fpair_fplot"','length': 10,'name': 'fcase_fazimuth_first_fpair_fplot','precision': 0,'type': 1},{'aggregate': 'first_value','delimiter': ',','input': '"scase_sazimuth_secound_spair_splot"','length': 10,'name': 'scase_sazimuth_secound_spair_splot','precision': 0,'type': 1},{'aggregate': 'first_value','delimiter': ',','input': '"case_border_count_plot"','length': 10,'name': 'case_border_count_plot','precision': 0,'type': 1},{'aggregate': 'sum','delimiter': ',','input': '"length_first_pair"','length': 10,'name': 'length_first_pair','precision': 2,'type': 6},{'aggregate': 'sum','delimiter': ',','input': '"length_secound_pair"','length': 10,'name': 'length_secound_pair','precision': 2,'type': 6}],
            'GROUP_BY': 'plot_number',
            'INPUT': outputs['scase_sazimuth_secound_spair_splot']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['agg_in_data_unregular_plot'] = processing.run('native:aggregate', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(41)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'FIELD_LENGTH': 2,
            'FIELD_NAME': 'select_longer_pair',
            'FIELD_PRECISION': 1,
            'FIELD_TYPE': 1,  
            'FORMULA': 'CASE\r\nWHEN "length_first_pair" > "length_secound_pair" THEN 1\r\nWHEN "length_first_pair" < "length_secound_pair" THEN 2\r\nELSE 0\r\nEND\r\n',
            'INPUT': outputs['agg_in_data_unregular_plot']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['select_longer_pair'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(42)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'DISCARD_NONMATCHING': False,
            'FIELD': 'plot_number',
            'FIELDS_TO_COPY': ['area_plot','case_border_form','case_length_first_pair_plot','case_length_secound_pair_plot','fcase_fazimuth_first_fpair_fplot','scase_sazimuth_secound_spair_splot','case_border_count_plot','select_longer_pair'],
            'FIELD_2': 'plot_number',
            'INPUT': outputs['plot_number']['OUTPUT'],
            'INPUT_2': outputs['select_longer_pair']['OUTPUT'],
            'METHOD': 1,  
            'PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['join_unregular_plot'] = processing.run('native:joinattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(43)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'CLASSFIELD': '',
            'FIELD': 'count_right_angle_fs_plot',
            'POINTS': outputs['right_angle_plot']['OUTPUT'],
            'POLYGONS': outputs['join_unregular_plot']['OUTPUT'],
            'WEIGHT': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['count_right_angle_fs_plot'] = processing.run('native:countpointsinpolygon', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(44)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'DISCARD_NONMATCHING': False,
            'FIELD': 'plot_number',
            'FIELDS_TO_COPY': ['case_azimuth_long_unrglr','length_break_first_pair'],
            'FIELD_2': 'plot_number',
            'INPUT': outputs['count_right_angle_fs_plot']['OUTPUT'],
            'INPUT_2': outputs['agg_preinput_eq_unregular']['OUTPUT'],
            'METHOD': 1,  
            'PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['join_all_plot'] = processing.run('native:joinattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(45)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'FIELD_LENGTH': 1,
            'FIELD_NAME': 'shape_evaluation',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 1,  
            'FORMULA': 'CASE\r\nWHEN "area_plot" >= 0 AND "area_plot" <= 1 AND "case_border_form" = TRUE AND "case_length_first_pair_plot" = TRUE AND "case_length_secound_pair_plot" = TRUE AND "fcase_fazimuth_first_fpair_fplot" = TRUE AND "scase_sazimuth_secound_spair_splot" = TRUE AND "case_border_count_plot" = TRUE AND "count_right_angle_fs_plot" = 4 THEN 2\r\nWHEN "area_plot" > 1 AND "area_plot" <= 2 AND "case_length_first_pair_plot" = TRUE AND "case_length_secound_pair_plot" = TRUE AND "fcase_fazimuth_first_fpair_fplot" = TRUE AND "scase_sazimuth_secound_spair_splot" = TRUE AND "case_border_count_plot" = TRUE AND "count_right_angle_fs_plot" = 4 THEN 2\r\nWHEN "area_plot" > 2 AND "area_plot" <= 5 AND "fcase_fazimuth_first_fpair_fplot" = TRUE AND "scase_sazimuth_secound_spair_splot" = TRUE AND "case_border_count_plot" = TRUE THEN 2\r\nWHEN "area_plot" > 5 AND "area_plot" <= 10 AND "case_border_count_plot" = TRUE AND "case_azimuth_long_unrglr" = TRUE THEN 2\r\nWHEN "area_plot" > 10 AND "case_border_count_plot" = TRUE THEN 2\r\nWHEN "area_plot" >= 0 AND "area_plot" <= 1 AND "case_azimuth_long_unrglr" = TRUE THEN 1\r\nWHEN "area_plot" > 1 AND "area_plot" <= 2 AND "case_azimuth_long_unrglr" = TRUE AND "length_break_first_pair" <= 1 THEN 1\r\nWHEN "area_plot" > 2 AND "area_plot" <= 5 AND "case_azimuth_long_unrglr" = TRUE AND "length_break_first_pair" <= 2 THEN 1 \r\nWHEN "area_plot" > 5 AND "area_plot" <= 10 AND "case_azimuth_long_unrglr" = TRUE AND "length_break_first_pair" <= 3 THEN 1 \r\nWHEN "area_plot" > 10 AND "case_azimuth_long_unrglr" = TRUE THEN 1\r\nELSE 0\r\nEND',
            'INPUT': outputs['join_all_plot']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['shape_evaluation'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(46)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'COLUMN': ['plot_number','area_plot','case_border_form','case_length_first_pair_plot','case_length_secound_pair_plot','fcase_fazimuth_first_fpair_fplot','scase_sazimuth_secound_spair_splot','case_border_count_plot','select_longer_pair','count_right_angle_fs_plot','case_azimuth_long_unrglr','length_break_first_pair'],
            'INPUT': outputs['shape_evaluation']['OUTPUT'],
            'OUTPUT': parameters['Ocena']
        }
        outputs['delete_un_column'] = processing.run('native:deletecolumn', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Ocena'] = outputs['delete_un_column']['OUTPUT']
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
