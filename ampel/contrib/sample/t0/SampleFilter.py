#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : ampel/contrib/hu/t0/SampleFilter.py
# License           : BSD-3-Clause
# Author            : m. giomi <matteo.giomi@desy.de>
# Date              : 06.06.2018
# Last Modified Date: 04.09.2018
# Last Modified By  : j. nordin <jnordin@physik.hu-berlin.de>

from numpy import exp, array
import logging
from urllib.parse import urlparse
from astropy.coordinates import SkyCoord
from astropy.table import Table
import sys
try:
	from catsHTM import cone_search
	doCat = True
except ImportError:
	doCat = False
from ampel.base.abstract.AbsAlertFilter import AbsAlertFilter

class SampleFilter(AbsAlertFilter):
	"""
		Sample AMPEL T0 filter, derived from the DecentFilter. It selects alerts based on:
			* numper of previous detections
			* subtraction FWHM and the difference between PSF and aperture magnitude
			* detection of proper-motion and paralax for coincidence sources in GAIA DR2

	"""

	# Static version info
	version = 0.1
        # This statement makes one of the default AMPEL resources available, here the catsHTM catalog collection (2018PASP..130g5002S)
	resources = ('catsHTM.default',)

	def __init__(self, on_match_t2_units, base_config=None, run_config=None, logger=None):
		"""
		"""
		if run_config is None or len(run_config) == 0:
			raise ValueError("Please check you run configuration")

		self.on_match_t2_units = on_match_t2_units
		self.logger = logger if logger is not None else logging.getLogger()

		config_params = (
			'MIN_NDET',					# number of previous detections
			'MAX_FWHM',					# sexctrator FWHM (assume Gaussian) [pix]
			'MAX_MAGDIFF',				# Difference: magap - magpsf [mag]
			'MAX_NBAD',					# number of bad pixels in a 5 x 5 pixel stamp
			'GAIA_RS',					# search radius for GAIA DR2 matching [arcsec]
			'GAIA_PM_SIGNIF',			# significance of proper motion detection of GAIA counterpart [sigma]
			'GAIA_PLX_SIGNIF',			# significance of parallax detection of GAIA counterpart [sigma]
			)
		for el in config_params:
			if el not in run_config:
				raise ValueError("Parameter %s missing, please check your channel config" % el)
			if run_config[el] is None:
				raise ValueError("Parameter %s is None, please check your channel config" % el)
			self.logger.info("Using %s=%s" % (el, run_config[el]))


		# ----- set filter proerties ----- #

		# history
		self.min_ndet 					= run_config['MIN_NDET']

		# Image quality
		self.max_fwhm					= run_config['MAX_FWHM']
		self.max_magdiff				= run_config['MAX_MAGDIFF']

		# astro
		self.gaia_rs					= run_config['GAIA_RS']
		self.gaia_pm_signif				= run_config['GAIA_PM_SIGNIF']
		self.gaia_plx_signif			= run_config['GAIA_PLX_SIGNIF']
		self.gaia_veto_gmag_min			= 12
		self.gaia_veto_gmag_max			= 18

		# technical
		if doCat:
			self.catshtm_path 			= urlparse(base_config['catsHTM.default']).path
			self.logger.info("using catsHTM files in %s"%self.catshtm_path)
		self.keys_to_check = ( 'fwhm', 'magdiff', 'ra', 'dec' )


	def _alert_has_keys(self, photop):
		"""
			check that given photopoint contains all the keys needed to filter
		"""
		for el in self.keys_to_check:
			if el not in photop:
				self.logger.debug("rejected: '%s' missing" % el)
				return False
			if photop[el] is None:
				self.logger.debug("rejected: '%s' is None" % el)
				return False
		return True





	def is_star_in_gaia(self, transient):
		"""
			match tranient position with GAIA DR2 and uses parallax
			and proper motion to evaluate star-likeliness

			returns: True (is a star) or False otehrwise.
		"""

		transient_coords = SkyCoord(transient['ra'], transient['dec'], unit='deg')
		srcs, colnames, colunits = cone_search(
											'GAIADR2',
											transient_coords.ra.rad, transient_coords.dec.rad,
											self.gaia_rs,
											catalogs_dir=self.catshtm_path)
		my_keys = ['RA', 'Dec', 'Mag_G', 'PMRA', 'ErrPMRA', 'PMDec', 'ErrPMDec', 'Plx', 'ErrPlx']
		if len(srcs) > 0:
			gaia_tab					= Table(srcs, names=colnames)
			gaia_tab					= gaia_tab[my_keys]
			gaia_coords					= SkyCoord(gaia_tab['RA'], gaia_tab['Dec'], unit='rad')

			# compute distance
			gaia_tab['DISTANCE']		= transient_coords.separation(gaia_coords).arcsec
			gaia_tab['DISTANCE_NORM']	= (
				1.8 + 0.6 * exp( (20 - gaia_tab['Mag_G']) / 2.05) > gaia_tab['DISTANCE'])
			gaia_tab['FLAG_PROX']		= [
											True if x['DISTANCE_NORM'] == True and
											(self.gaia_veto_gmag_min <= x['Mag_G'] <= self.gaia_veto_gmag_max) else
											False for x in gaia_tab
											]

			# check for proper motion and parallax conditioned to distance
			gaia_tab['FLAG_PMRA']		= abs(gaia_tab['PMRA']  / gaia_tab['ErrPMRA']) > self.gaia_pm_signif
			gaia_tab['FLAG_PMDec']		= abs(gaia_tab['PMDec'] / gaia_tab['ErrPMDec']) > self.gaia_pm_signif
			gaia_tab['FLAG_Plx']		= abs(gaia_tab['Plx']   / gaia_tab['ErrPlx']) > self.gaia_plx_signif
			if (any(gaia_tab['FLAG_PMRA'] == True) or
				any(gaia_tab['FLAG_PMDec'] == True) or
				any(gaia_tab['FLAG_Plx'] == True)) and any(gaia_tab['FLAG_PROX'] == True):
				return True
		return False


	def apply(self, alert):
		"""
		Mandatory implementation.
		To exclude the alert, return *None*
		To accept it, either return
			* self.on_match_t2_units
			* or a custom combination of T2 unit names
		"""

		# --------------------------------------------------------------------- #
		#					CUT ON THE HISTORY OF THE ALERT						#
		# --------------------------------------------------------------------- #

		npp = len(alert.pps)
		if npp < self.min_ndet:
			self.logger.debug("rejected: %d photopoints in alert (minimum required %d)"%
				(npp, self.min_ndet))
			return None


		# --------------------------------------------------------------------- #
		#							IMAGE QUALITY CUTS							#
		# --------------------------------------------------------------------- #

		latest = alert.pps[0]
		if not self._alert_has_keys(latest):
			return None


		if latest['fwhm'] > self.max_fwhm:
			self.logger.debug("rejected: fwhm %.2f above threshod (%.2f)"%
				(latest['fwhm'], self.max_fwhm))
			return None

		if abs(latest['magdiff']) > self.max_magdiff:
			self.logger.debug("rejected: magdiff (AP-PSF) %.2f above threshod (%.2f)"%
				(latest['magdiff'], self.max_magdiff))
			return None

		# --------------------------------------------------------------------- #
		#								ASTRONOMY								#
		# --------------------------------------------------------------------- #


		# check with gaia
		if self.gaia_rs>0:
			if not doCat:
				sys.exit("Cannot match to Gaia without catsHTM!")
			if self.is_star_in_gaia(latest):
				self.logger.debug("rejected: within %.2f arcsec from a GAIA star (PM of PLX)" %
					(self.gaia_rs))
				return None

		# congratulation alert! you made it!
		self.logger.debug("Alert %s accepted. Latest pp ID: %d"%(alert.tran_id, latest['candid']))
		for key in self.keys_to_check:
			self.logger.debug("{}: {}".format(key, latest[key]))
		return self.on_match_t2_units

