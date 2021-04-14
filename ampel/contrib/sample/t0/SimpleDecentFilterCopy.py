#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-contrib-HU/ampel/contrib/sample/t0/SimpleDecentFilterCopy.py
# License           : BSD-3-Clause
# Author            : m. giomi <matteo.giomi@desy.de>
# Date              : 12.02.2019
# Last Modified Date: 04.04.2021
# Last Modified By  : jno

from numpy import array
from astropy.coordinates import SkyCoord
from ampel.abstract.AbsAlertFilter import AbsAlertFilter
from ampel.alert.PhotoAlert import PhotoAlert


class SimpleDecentFilterCopy(AbsAlertFilter[PhotoAlert]):
	"""
	General-purpose filter devloped alongside DecentFilter but without use of external 
        catalogs. It selects alerts based on:
	* numper of previous detections
	* positive subtraction flag
	* loose cuts on image quality (fwhm, elongation, number of bad pixels, and the
	difference between PSF and aperture magnitude)
	* distance to known SS objects
	* (d) real-bogus
        * Whether it seems a PS source exists at the transient position (as per alert properties).
	"""

	# history
	min_ndet: int = 2 # number of previous detections
	min_tspan: float = 0.02 # minimum duration of alert detection history [days]
	max_tspan: float = 25. # maximum duration of alert detection history [days]

	# Image quality
	min_drb: float = 0. # deep learning real bogus score
	min_rb: float = 0.3 # real bogus score
	max_fwhm: float = 5. # sexctrator FWHM (assume Gaussian) [pix]
	max_elong: float = 1.4 # Axis ratio of image: aimage / bimage
	max_magdiff: float = 0.4 # Difference: magap - magpsf [mag]
	max_nbad: int = 0 # number of bad pixels in a 5 x 5 pixel stamp

	# astro
	min_sso_dist: float = 20. # distance to nearest solar system object [arcsec]
	min_gal_lat: float = 0. # minium distance from galactic plane. Set to negative to disable cut.
	ps1_sgveto_rad: float = 2. # maximum distance to closest PS1 source for SG score veto [arcsec]
	ps1_sgveto_th: float = 0.8 # maximum allowed SG score for PS1 source within PS1_SGVETO_RAD
	ps1_confusion_rad: float = 1. # reject alerts if the three PS1 sources are all within this radius [arcsec]
	ps1_confusion_sg_tol: float = 0.5 # and if the SG score of all of these 3 sources is within this tolerance to 0.5


	def post_init(self):

		# feedback
		for k in self.__annotations__:
			self.logger.info(f"Using {k}={getattr(self, k)}")

		self.keys_to_check = (
			'fwhm', 'elong', 'magdiff', 'nbad', 'distpsnr1', 'sgscore1', 'distpsnr2',
			'sgscore2', 'distpsnr3', 'sgscore3', 'isdiffpos', 'ra', 'dec', 'rb', 'ssdistnr'
		)


	def _alert_has_keys(self, photop):
		"""
		Check that given photopoint contains all the keys needed to filter
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
		""" Compute galactic latitude of the transient """
		coordinates = SkyCoord(transient['ra'], transient['dec'], unit='deg')
		b = coordinates.galactic.b.deg
		return b


	def is_star_in_PS1(self, transient):
		"""
		Apply combined cut on sgscore1 and distpsnr1 to reject the transient if
		there is a PS1 star-like object in it's immediate vicinity
		"""
		if (
			transient['distpsnr1'] < self.ps1_sgveto_rad and
			transient['sgscore1'] > self.ps1_sgveto_th
		):
			return True
		return False


	def is_confused_in_PS1(self, transient):
		"""
		Check in PS1 for source confusion, which can induce subtraction artifatcs.
		These cases are selected requiring that all three PS1 cps are in the imediate
		vicinity of the transient and their sgscore to be close to 0.5 within given tolerance.
		"""
		sg1, sg2, sg3 = transient['sgscore1'], transient['sgscore2'], transient['sgscore3']
		d1, d2, d3 = transient['distpsnr1'], transient['distpsnr2'], transient['distpsnr3']
		very_close = max([d1, d2, d3]) < self.ps1_confusion_rad
		sg_confused = abs(array([sg1, sg2, sg3]) - 0.5).max() < self.ps1_confusion_sg_tol
		if sg_confused and very_close:
			return True
		return False


	def apply(self, alert: PhotoAlert):
		"""
		Mandatory implementation.
		Return values:
		- None or False: reject the alert
		- True: accept the alert and create all defined t2 documents
		- positive integer: accept the alert and create t2 documents associated with provided group id
		- negative integer: filter (own) rejection code (must not exceed 255)
		"""

		# CUT ON THE HISTORY OF THE ALERT
		#################################

		npp = len(alert.pps)
		if npp < self.min_ndet:
			#self.logger.debug("rejected: %d photopoints in alert (minimum required %d)"% (npp, self.min_ndet))
			self.logger.info(None, extra={'nDet': npp})
			return None

		# cut on length of detection history
		detections_jds = alert.get_values('jd', data='pps')
		det_tspan = max(detections_jds) - min(detections_jds)
		if not (self.min_tspan < det_tspan < self.max_tspan):
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

		if self.min_drb > 0. and latest['drb'] < self.min_drb:
			self.logger.info(None, extra={'drb': latest['drb']})
			return None


		if latest['rb'] < self.min_rb:
			#self.logger.debug("rejected: RB score %.2f below threshod (%.2f)"% (latest['rb'], self.min_rb))
			self.logger.info(None, extra={'rb': latest['rb']})
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
		if 0 <= latest['ssdistnr'] < self.min_sso_dist:
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

		# congratulation alert! you made it!
		#self.logger.debug("Alert %s accepted. Latest pp ID: %d"%(alert.tran_id, latest['candid']))
		self.logger.debug("Alert accepted", extra={'latestPpId': latest['candid']})

		#for key in self.keys_to_check:
		#	self.logger.debug("{}: {}".format(key, latest[key]))

		return True
