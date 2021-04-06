#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : ampel/contrib/sample/t2/T2SNcosmoComp.py
# License           : BSD-3-Clause
# Author            : jnordin@physik.hu-berlin.de
# Date              : 03.04.2021
# Last Modified Date: 03.04.2021
# Last Modified By  : jnordin@physik.hu-berlin.de

from typing import Dict, List, Optional, Sequence, Any, Tuple
import numpy as np
import sncosmo
from ampel.type import T2UnitResult
from ampel.view.LightCurve import LightCurve
from astropy.table import Table
from ampel.abstract.AbsLightCurveT2Unit import AbsLightCurveT2Unit




class T2SNcosmoComp(AbsLightCurveT2Unit):
    """

    This unit tests whether a "target" SNcosmo source provides a better match to a LightCurve
    compared with a "base" source. 
    A fit quality test is also done.

    This class is still only rudimentary. In particular:
    - MW or host galaxy reddening not accounted for!
    - All models assumed to be part of the standard SNcosmo registry.
    - Assumes input lightcurve contains AB magnitudes.
    - Model fit boundaries not propagated to fit.
    - ...
    
    The run method, applied to a LightCurve, will return a dict (T2UnitResult).
    In this 
       'target_match':True
    for lightcurves fulfilling the target criteria. 
    (For this sample case we also include the fitted model).
    
    """

    # Parameters that can, and in some cases need to be configured by the user
    # Name of model for the target search. If not available in the registery, SNcosmo will try to download
    target_model_name: str
    # Name of base comparison model
    base_model_name: str
    # Chi^2 / dof cut for acceptance as potential model
    chi2dof_cut: float = 3.
    # The target model chi^2/dof has to be better, after scaling with this factor  
    chicomp_scaling: float = 1.
    # Redshift bound for template fit
    zbound: Tuple[float, float] = (0,0.2)


    def post_init(self)-> None:
        """
        Retrieve models.
        """
        self.target_model = sncosmo.Model(source=self.target_model_name)
        self.base_model = sncosmo.Model(source=self.base_model_name)
    
        
    def run(self, light_curve: LightCurve) -> T2UnitResult:
        """
        Parameters
        -----------
        light_curve: "ampel.view.LightCurve" instance.
        See the LightCurve docstring for more info.

        Returns
        -------
        dict
        """

        self.logger.info('Fitting %s'%(light_curve.stock_id) )

        # Create SNCosmo input table
        phot = np.asarray( light_curve.get_ntuples(('jd','magpsf','sigmapsf','fid')) )
        phot_tab = Table(phot,names=('jd','magpsf','sigmapsf','fid'))
        phot_tab['band'] = 'ztfband'
        for fid, fname in zip( [1,2,3], ['ztfg','ztfr','ztfi']):
            phot_tab['band'][phot_tab['fid']==fid] = fname
        phot_tab['flux'] = 10 ** (-(phot_tab['magpsf'] - 25) / 2.5)
        phot_tab['fluxerr'] = np.abs(phot_tab['flux'] * (-phot_tab['sigmapsf'] / 2.5 * np.log(10)))
        phot_tab['zp'] = 25
        phot_tab['zpsys'] = 'ab'
        
        # Fit base match
        try:
            result, fitted_model = sncosmo.fit_lc(
                phot_tab, self.base_model, self.base_model.param_names, bounds={'z':self.zbound})  
            chidof_base = result.chisq / result.ndof
        except RuntimeError:
            # We interpret a poor fit a a weird lightcurve, and exit
            self.logger.info("Base fit fails",extra={"stock_id":light_curve.stock_id})
            return {'chidof_base':-1,'chidof_target':0, 'model_match': False, 'info': 'basefit fails'}

        
        # Fit target source
        try:
            result, fitted_model = sncosmo.fit_lc(
                phot_tab, self.target_model, self.target_model.param_names, bounds={'z':self.zbound}  )  
            chidof_target = result.chisq / result.ndof
        except RuntimeError:
            # We interpret a poor fit a a weird lightcurve, and exit
            self.logger.info("Target fit fails",extra={"stock_id":light_curve.stock_id})
            return {'chidof_base':chidof_base,'chidof_target':-1, 'model_match': False, 'info': 'targetfit fails'}
        
        
        # Gather information to propagate / log
        fit_info = {'chidof_base':chidof_base,'chidof_target':chidof_target,
            'base_model':self.base_model_name, 'target_model':self.target_model_name}

        # Crude decision made
        if chidof_target>self.chi2dof_cut:
            fit_info['target_match'] = False
            fit_info['info'] = 'Poor lc fit'
        elif chidof_base < ( chidof_target * self.chicomp_scaling ):
            fit_info['target_match'] = False
            fit_info['info'] = 'Better base fit'
        else:
            fit_info['target_match'] = True
            fit_info['info'] = 'Good match'
        
        
        return fit_info
