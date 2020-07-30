#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-contrib-HU/ampel/contrib/hu/t0/DecentFilter.py
# License           : BSD-3-Clause
# Author            : m. giomi <matteo.giomi@desy.de>
# Date              : 06.06.2018
# Last Modified Date: 05.02.2020
# Last Modified By  : vb <vbrinnel@physik.hu-berlin.de>

from numpy import exp, asarray
from typing import Optional, Union
from astropy.table import Table
from astropy.coordinates import SkyCoord

from ampel.contrib.groupname import catshtm_server
from ampel.alert.PhotoAlert import PhotoAlert
from ampel.abstract.AbsAlertFilter import AbsAlertFilter


class DecentFilterCopy(AbsAlertFilter[PhotoAlert]):
	"""
	General-purpose filter with ~ 0.6% acceptance. It selects alerts based on:
	* numper of previous detections
	* positive subtraction flag
	* loose cuts on image quality (fwhm, elongation, number of bad pixels, and the
		difference between PSF and aperture magnitude)
	* distance to known SS objects
	* real-bogus
	* detection of proper-motion and paralax for coincidence sources in GAIA DR2

	The filter has a very weak dependence on the real-bogus score and it is independent
	on the provided PS1 star-galaxy classification.
	"""

	require = ('ampel-contrib-sample/catsHTM.default', )

	# History
	min_ndet: int # number of previous detections
	min_tspan: float # minimum duration of alert detection history [days]
	max_tspan: float # maximum duration of alert detection history [days]

	# Image quality
	min_drb: float = 0. # deep learning real bogus score
	min_rb: float # real bogus score
	max_fwhm: float # sexctrator FWHM (assume Gaussian) [pix]
	max_elong: float # Axis ratio of image: aimage / bimage
	max_magdiff: float # Difference: magap - magpsf [mag]
	max_nbad: int # number of bad pixels in a 5 x 5 pixel stamp

	# Astro
	min_sso_dist: float # distance to nearest solar system object [arcsec]
	min_gal_lat: float # minium distance from galactic plane. Set to negative to disable cut.

	# PS1
	ps1_sgveto_rad: float # maximum distance to closest PS1 source for SG score veto [arcsec]
	ps1_sgveto_th: float # maximum allowed SG score for PS1 source within PS1_SGVETO_RAD
	ps1_confusion_rad: float # reject alerts if the three PS1 sources are all within this radius [arcsec]
	ps1_confusion_sg_tol: float # and if the SG score of all of these 3 sources is within this tolerance to 0.5

	# Gaia
	gaia_rs: float # search radius for GAIA DR2 matching [arcsec]
	gaia_pm_signif: float # significance of proper motion detection of GAIA counterpart [sigma]
	gaia_plx_signif: float # significance of parallax detection of GAIA counterpart [sigma]
	gaia_veto_gmag_min: float # min gmag for normalized distance cut of GAIA counterparts [mag]
	gaia_veto_gmag_max: float # max gmag for normalized distance cut of GAIA counterparts [mag]
	gaia_excessnoise_sig_max: float	# maximum allowed noise (expressed as significance) for Gaia match to be trusted.


	def post_init(self):

		# feedback
		for k in self.__annotations__:
			self.logger.info(f"Using {k}={getattr(self, k)}")

		self.catshtm = catshtm_server.get_client(
			*self.resource.values()
		)

		# To make this tenable we should create this list dynamically depending on what entries are required
		# by the filter. Now deciding not to include drb in this list, eg.
		self.keys_to_check = (
			'fwhm', 'elong', 'magdiff', 'nbad', 'distpsnr1', 'sgscore1', 'distpsnr2',
			'sgscore2', 'distpsnr3', 'sgscore3', 'isdiffpos', 'ra', 'dec', 'rb', 'ssdistnr'
		)


	def _alert_has_keys(self, photop) -> bool:
		"""
		check that given photopoint contains all the keys needed to filter
		"""
		for el in self.keys_to_check:
			if el not in photop:
				self.logger.info(None, extra={"missing": el})
				return False
			if photop[el] is None:
				self.logger.info(None, extra={"isNone": el})
				return False
		return True


	def get_galactic_latitude(self, transient):
		"""
		compute galactic latitude of the transient
		"""
		coordinates = SkyCoord(transient['ra'], transient['dec'], unit='deg')
		return coordinates.galactic.b.deg


	def is_star_in_PS1(self, transient) -> bool:
		"""
		apply combined cut on sgscore1 and distpsnr1 to reject the transient if
		there is a PS1 star-like object in it's immediate vicinity
		"""

		#TODO: consider the case of alert moving wrt to the position of a star
		# maybe cut on the minimum of the distance!
		return transient['distpsnr1'] < self.ps1_sgveto_rad and \
			transient['sgscore1'] > self.ps1_sgveto_th


	def is_confused_in_PS1(self, transient) -> bool:
		"""
		check in PS1 for source confusion, which can induce subtraction artifatcs.
		These cases are selected requiring that all three PS1 cps are in the imediate
		vicinity of the transient and their sgscore to be close to 0.5 within given tolerance.
		"""
		very_close = max(
			transient['distpsnr1'],
			transient['distpsnr2'],
			transient['distpsnr3']
		) < self.ps1_confusion_rad

		# Update 31.10.19: avoid costly numpy cast
		# Old:
		# In: %timeit abs(array([sg1, sg2, sg3]) - 0.5 ).max()
		# Out: 5.79 µs ± 80.5 ns per loop (mean ± std. dev. of 7 runs, 100000 loops each)
		# New:
		# In: %timeit max(abs(sg1-0.5), abs(sg2-0.5), abs(sg3-0.5))
		# Out: 449 ns ± 7.01 ns per loop (mean ± std. dev. of 7 runs, 1000000 loops each)

		sg_confused = max(
			abs(transient['sgscore1'] - 0.5),
			abs(transient['sgscore2'] - 0.5),
			abs(transient['sgscore3'] - 0.5)
		) < self.ps1_confusion_sg_tol

		return sg_confused and very_close


	def is_star_in_gaia(self, transient) -> bool:
		"""
		match tranient position with GAIA DR2 and uses parallax
		and proper motion to evaluate star-likeliness
		returns: True (is a star) or False otehrwise.
		"""

		transient_coords = SkyCoord(
			transient['ra'], transient['dec'], unit='deg'
		)

		srcs, colnames, colunits = self.catshtm.cone_search(
			'GAIADR2', transient_coords.ra.rad,
			transient_coords.dec.rad, self.gaia_rs
		)

		my_keys = [
			'RA', 'Dec', 'Mag_G', 'PMRA', 'ErrPMRA', 'PMDec',
			'ErrPMDec', 'Plx', 'ErrPlx', 'ExcessNoiseSig'
		]

		if len(srcs) > 0:

			gaia_tab = Table(asarray(srcs), names=colnames)
			gaia_tab = gaia_tab[my_keys]
			gaia_coords = SkyCoord(gaia_tab['RA'], gaia_tab['Dec'], unit='rad')

			# compute distance
			gaia_tab['DISTANCE'] = transient_coords.separation(gaia_coords).arcsec
			gaia_tab['DISTANCE_NORM'] = 1.8 + 0.6 * exp((20 - gaia_tab['Mag_G']) / 2.05) > gaia_tab['DISTANCE']
			gaia_tab['FLAG_PROX'] = [
				x['DISTANCE_NORM'] and
				self.gaia_veto_gmag_min <= x['Mag_G'] <= self.gaia_veto_gmag_max
				for x in gaia_tab
			]

			# check for proper motion and parallax conditioned to distance
			gaia_tab['FLAG_PMRA'] = abs(gaia_tab['PMRA'] / gaia_tab['ErrPMRA']) > self.gaia_pm_signif
			gaia_tab['FLAG_PMDec'] = abs(gaia_tab['PMDec'] / gaia_tab['ErrPMDec']) > self.gaia_pm_signif
			gaia_tab['FLAG_Plx'] = abs(gaia_tab['Plx'] / gaia_tab['ErrPlx']) > self.gaia_plx_signif

			# take into account precison of the astrometric solution via the ExcessNoise key
			gaia_tab['FLAG_Clean'] = gaia_tab['ExcessNoiseSig'] < self.gaia_excessnoise_sig_max

			# select just the sources that are close enough and that are not noisy
			gaia_tab = gaia_tab[gaia_tab['FLAG_PROX']]
			gaia_tab = gaia_tab[gaia_tab['FLAG_Clean']]

			# among the remaining sources there is anything with
			# significant proper motion or parallax measurement
			if (
				any(gaia_tab['FLAG_PMRA'] == True) or
				any(gaia_tab['FLAG_PMDec'] == True) or
				any(gaia_tab['FLAG_Plx'] == True)
			):
				return True

		return False


	# Override
	def apply(self, alert: PhotoAlert) -> Optional[Union[bool, int]]:
		"""
		Mandatory implementation.
		To exclude the alert, return *None*
		To accept it, either return
		* self.on_match_t2_units
		* or a custom combination of T2 unit names
		"""

		# CUT ON THE HISTORY OF THE ALERT
		#################################

		npp = len(alert.pps)
		if npp < self.min_ndet:
			#self.logger.debug("rejected: %d photopoints in alert (minimum required %d)"% (npp, self.min_ndet))
			self.logger.info(None, extra={'nDet': npp})
			return None

		# cut on length of detection history
		detections_jds = alert.get_values('jd')
		det_tspan = max(detections_jds) - min(detections_jds)
		if not (self.min_tspan <= det_tspan <= self.max_tspan):
			#self.logger.debug("rejected: detection history is %.3f d long, \
			# requested between %.3f and %.3f d"% (det_tspan, self.min_tspan, self.max_tspan))
			self.logger.info(None, extra={'tSpan': det_tspan})
			return None


		# IMAGE QUALITY CUTS
		####################

		latest = alert.pps[0]
		if not self._alert_has_keys(latest):
			return None

		if latest['isdiffpos'] == 'f' or latest['isdiffpos'] == '0':
			#self.logger.debug("rejected: 'isdiffpos' is %s", latest['isdiffpos'])
			self.logger.info(None, extra={'isdiffpos': latest['isdiffpos']})
			return None

		if latest['rb'] < self.min_rb:
			#self.logger.debug("rejected: RB score %.2f below threshod (%.2f)"% (latest['rb'], self.min_rb))
			self.logger.info(None, extra={'rb': latest['rb']})
			return None

		if self.min_drb > 0. and latest['drb'] < self.min_drb:
			#self.logger.debug("rejected: RB score %.2f below threshod (%.2f)"% (latest['rb'], self.min_rb))
			self.logger.info(None, extra={'drb': latest['drb']})
			return None

		if latest['fwhm'] > self.max_fwhm:
			#self.logger.debug("rejected: fwhm %.2f above threshod (%.2f)"% (latest['fwhm'], self.max_fwhm))
			self.logger.info(None, extra={'fwhm': latest['fwhm']})
			return None

		if latest['elong'] > self.max_elong:
			#self.logger.debug("rejected: elongation %.2f above threshod (%.2f)"% (latest['elong'], self.max_elong))
			self.logger.info(None, extra={'elong': latest['elong']})
			return None

		if abs(latest['magdiff']) > self.max_magdiff:
			#self.logger.debug("rejected: magdiff (AP-PSF) %.2f above threshod (%.2f)"% (latest['magdiff'], self.max_magdiff))
			self.logger.info(None, extra={'magdiff': latest['magdiff']})
			return None


		# ASTRONOMY
		###########

		# check for closeby ss objects
		if (0 <= latest['ssdistnr'] < self.min_sso_dist):
			#self.logger.debug("rejected: solar-system object close to transient (max allowed: %d)."% (self.min_sso_dist))
			self.logger.info(None, extra={'ssdistnr': latest['ssdistnr']})
			return None

		# cut on galactic latitude
		b = self.get_galactic_latitude(latest)
		if abs(b) < self.min_gal_lat:
			#self.logger.debug("rejected: b=%.4f, too close to Galactic plane (max allowed: %f)."% (b, self.min_gal_lat))
			self.logger.info(None, extra={'galPlane': abs(b)})
			return None

		# check ps1 star-galaxy score
		if self.is_star_in_PS1(latest):
			#self.logger.debug("rejected: closest PS1 source %.2f arcsec away with sgscore of %.2f"% (latest['distpsnr1'], latest['sgscore1']))
			self.logger.info(None, extra={'distpsnr1': latest['distpsnr1']})
			return None

		if self.is_confused_in_PS1(latest):
			#self.logger.debug("rejected: three confused PS1 sources within %.2f arcsec from alert."% (self.ps1_confusion_rad))
			self.logger.info(None, extra={'ps1Confusion': True})
			return None

		# check with gaia
		if self.gaia_rs > 0 and self.is_star_in_gaia(latest):
			#self.logger.debug("rejected: within %.2f arcsec from a GAIA start (PM of PLX)" % (self.gaia_rs))
			self.logger.info(None, extra={'gaiaIsStar': True})
			return None

		# congratulation alert! you made it!
		#self.logger.debug("Alert %s accepted. Latest pp ID: %d"%(alert.tran_id, latest['candid']))
		self.logger.debug(
			"Alert accepted",
			extra={'latestPpId': latest['candid']}
		)

		#for key in self.keys_to_check:
		#	self.logger.debug("{}: {}".format(key, latest[key]))

		return True
