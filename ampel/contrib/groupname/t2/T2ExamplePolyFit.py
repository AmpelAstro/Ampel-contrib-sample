#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : ampel/contrib/hu/examples/t2/T2ExamplePolyFit.py
# License           : BSD-3-Clause
# Author            : vb <vbrinnel@physik.hu-berlin.de>
# Date              : 10.02.2018
# Last Modified Date: 14.04.2020
# Last Modified By  : vb <vbrinnel@physik.hu-berlin.de>

import numpy
from typing import Union
from ampel.view.LigthCurve import LigthCurve
from ampel.t2.T2RunState import T2RunState
from ampel.t2.T2UnitResult import T2UnitResult
from ampel.abstract.AbsLightCurveT2Unit import AbsLightCurveT2Unit


class T2ExamplePolyFit(AbsLightCurveT2Unit):
	"""
	Polynomial fitting.
	Fits data using numpy 'polyfit'
	"""

	version: float = 1.1
	author: str = "ztf-software@desy.de"
		
	# Polynom degree used for numpy.polyfit 
	degree: int = 5

	def run(self, lightcurve: LigthCurve) -> Union[T2UnitResult, T2RunState]:
		"""
		:param light_curve: see LightCurve docstring for more info.
		:returns: a dict instance containing the values to be saved into the DB
		-> IMPORTANT: the dict *must* be BSON serializable, that is:
			import bson
			bson.BSON.encode(<dict instance to be returned>)
		must not throw a InvalidDocument Exception
		Alternatively, one of the following T2RunState (int) flag member can be retuned:
		BAD_CONFIG, ERROR, EXCEPTION
		"""

		x = lightcurve.get_values("obs_date")
		y = lightcurve.get_values("mag")
		p = numpy.polyfit(x, y, self.degree)
		chi_squared = numpy.sum((numpy.polyval(p, x) - y) ** 2)

		self.logger.info("Please use 'self.logger' for logging")
		self.logger.debug("By doing so, log entries will be automatically recorded into the database")

		return {
			"result": {
				"polyfit": list(p),
				"chi2": chi_squared
			}
		}
	
