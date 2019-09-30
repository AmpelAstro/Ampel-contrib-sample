#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : ampel/contrib/hu/examples/t2/T2ExamplePolyFit.py
# License           : BSD-3-Clause
# Author            : vb <vbrinnel@physik.hu-berlin.de>
# Date              : 10.02.2018
# Last Modified Date: 22.09.2018
# Last Modified By  : vb <vbrinnel@physik.hu-berlin.de>

from ampel.base.abstract.AmpelABC import AmpelABC, abstractmethod
from ampel.base.abstract.AbsT2Unit import AbsT2Unit
import numpy

class T2ExamplePolyFit(AbsT2Unit):
	"""
	Polynomial fitting
	Fits data using numpy 'polyfit'
	"""

	version = 1.0
	author = "ztf-software@desy.de"

	def __init__(self, logger, base_config):
		"""
		'logger': instance of logging.Logger (std python module 'logging')
			-> example usage: logger.info("this is a log message")

		'base_config': optional dict with keys given by the `resources` property of the class
		"""

		# Save the logger as instance variable
		self.logger = logger

	def run(self, light_curve, run_config):
		"""
		'light_curve': instance of ampel.base.LightCurve. See LightCurve docstring for more info.

		'run_config': dict instance containing run parameters defined in ampel config section:
			t2_run_config->POLYFIT_[run_config_id]->runConfig
			whereby the run_config_id value is defined in the associated t2 document.
			In the case of POLYFIT, run_config_id would be either 'default' or 'advanced'.
			A given channel (say HU_SN_IA) could use the runConfig 'default' whereas
			another channel (say OKC_SNIIP) could use the runConfig 'advanced'

		This method must return either:
			* A dict instance containing the values to be saved into the DB
				-> IMPORTANT: the dict *must* be BSON serializable, that is:
					import bson
					bson.BSON.encode(<dict instance to be returned>)
				must not throw a InvalidDocument Exception
			* One of these T2RunStates flag member:
				MISSING_INFO:  reserved for a future ampel extension where
							   T2s results could depend on each other
				BAD_CONFIG:	   Typically when run_config is not set properly
				ERROR:		   Generic error
				EXCEPTION:     An exception occured
		"""

		x = light_curve.get_values("obs_date")
		y = light_curve.get_values("mag")
		p = numpy.polyfit(x, y, run_config['degree'])
		chi_squared = numpy.sum((numpy.polyval(p, x) - y) ** 2)

		self.logger.info("Please use 'self.logger' for logging")
		self.logger.debug("By doing so, log entries will be automatically recorded into the database")

		return {
			"polyfit": list(p),
			"chi2": numpy.sum((numpy.polyval(p, x) - y) ** 2)
		}
