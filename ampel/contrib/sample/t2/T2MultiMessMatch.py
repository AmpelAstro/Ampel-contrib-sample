#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : ampel/contrib/sample/t2/T2MultiMessMatch.py
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
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.table import Table
from astropy.time import Time
from ampel.abstract.AbsLightCurveT2Unit import AbsLightCurveT2Unit



class T2MultiMessMatch(AbsLightCurveT2Unit):
    """

    Sample unit demonstrating how a comparison with a Multi Messenger alert _could_ be done.
    
    Will compare position, time and energy. 

    The post_init method here uses a sample position, but can be overwritten to read arbitary
    transient source.
    
    """

    # Parameters that can, and in some cases need to be configured by the user
    temporal_pull_scaling: float
    spatial_pull_scaling: float
    energy_pull_scaling: float
    match_where: str = 'latest'



    def post_init(self)-> None:
        """
        Retrieve a list of potential MM counterparts. Could be done through syncing with external
        source list or internal watchlist.

        The single position and energy structure can be replaced with more complex e.g. MOC regions
        or SEDs.
        """
        self.mm_list = [ {'ra': 15.9*u.deg, 'dec': 45*u.deg, 'pos_error': 1*u.deg,
                          'time': Time(2459100, format='jd'), 'time_error': 0.1*u.d, 
                          'ab_mag': 17, 'ab_mag_errr': 0.5, 'mm_ID':'sample_mm_alert'} ]





    
        
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

        self.logger.info('MMmatch: {}'.format(light_curve.stock_id) )

        # Extract transient comparison properties
        tdata = light_curve.get_ntuples( ('ra','dec','jd','magpsf','sigmapsf'))
        tdata.sort(key=lambda x: x[2])
        if self.match_where == 'first':
            matchphot = tdata[0]
        elif self.match_where == 'latest':
            matchphot = tdata[-1]
        elif self.match_where == 'mean':
            matchphot = np.array(tdata).mean(axis=0)
        else:
            raise ValueError("No valid match_where property set")
        opt_pos = SkyCoord(matchphot[0], matchphot[1], unit="deg" )

        # Retrieve match regions
        self.logger.info('Checking {} matches'.format(len(self.mm_list)) )
        
	# Evaluate matches
        t2_output = { 'matches' : [], 'best_match' : 10**30 }
        for mm_match in self.mm_list:
            self.logger.info('Checking MM alert {}'.format(mm_match['mm_ID']) )
            # Position
            ang_diff = float( opt_pos.separation( SkyCoord( mm_match['ra'], mm_match['dec']) ) / u.deg )
            ang_pull = ang_diff / float(mm_match['pos_error']/ u.deg ) * self.spatial_pull_scaling
            self.logger.info('Angular separtion {:.3f} with pull {:.2f}'.format(ang_diff,ang_pull) )
            # Time
            t_diff = float( (Time(matchphot[2], format='jd')-mm_match['time']).jd )
            t_pull = np.abs( t_diff ) / float(mm_match['time_error']/u.d ) * self.temporal_pull_scaling 
            self.logger.info('Time separtion {:.3f} with pull {:.2f}'.format(t_diff,t_pull) )
            # Energy
            e_diff = float( matchphot[3]-mm_match['ab_mag'] )
            e_pull = np.abs(e_diff) / float(mm_match['ab_mag_errr'] * matchphot[4] ) * self.energy_pull_scaling 
            self.logger.info('Energy separtion {:.3f} with pull {:.2f}'.format(e_diff,e_pull) )
            # Evaluate
            comb_pull = ang_pull * t_pull * e_pull
            self.logger.info('Combined pull {:.2f}'.format(comb_pull) )
            if comb_pull < t2_output['best_match']:
                t2_output['best_match'] = comb_pull
            t2_output['matches'].append( 
                {'ang_diff': ang_diff , 'ang_pull' : ang_pull, 't_diff':t_diff, 't_pull':t_pull,
                   'e_diff': e_diff, 'e_pull': e_pull, 'comb_pull': comb_pull, 'mm_ID': mm_match['mm_ID'] } 
) 
                


        
        return t2_output
