#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : ampel/contrib/sample/t3/T3HelloWorld.py
# License           : BSD-3-Clause
# Author            : jnordin@physik.hu-berlin.de
# Date              : 15.07.2019
# Last Modified Date: 04.04.2021
# Last Modified By  : jno 

from typing import Any, Dict, List, Optional, Tuple
from ampel.abstract.AbsT3Unit import AbsT3Unit
from ampel.struct.JournalTweak import JournalTweak
from ampel.view.TransientView import TransientView
from ampel.ztf.util.ZTFIdMapper import to_ampel_id, to_ztf_id
from ampel.type import StockId


class T3HelloWorld(AbsT3Unit):
    """
    A T3 unit is provided with TransientView summaries of transients.
    Typically, these have been selected based on some (T2) properties.
    Each T3 unit is executed as dictated by the scheduler, and can vary between
    semi-instantaneous reaction (e.g. every minute) to monthly summaries.

    All transients provided to this unit will trigger reactions. It is assumed that 
    selection and filtering has taken place in the T2 and through a
    T3FilteringStockSelector-like selection
    """


    # List of T2 unit names which should be collected for reaction
    t2info_from : List[str] = []



    def react(
        self, tran_view: TransientView, info: Dict[str, Any]
    ) -> Tuple[bool, Optional[Dict[str,Any]]]:
        """ Trigger a test slack report """

        success = False

        ztf_name = to_ztf_id(tran_view.id)
        msg = "T3HelloWorld says: Do something with %s. Provided info %s" % (
            ztf_name,
            info,
        )
        # This message would for a real unit be sent to e.g. slack, tns, gcn etc
        print(msg)
        success = True

        # Document what we did
        jcontent = {"reaction": "printed to stdout", "success": success}

        return success, jcontent

    def collect_info(self, tran_view: TransientView) -> Optional[Dict[str, Any]]:
        """
        Create an information dict from T2 outputs, which can be used by reactors.
        """

        info: Dict[str, Any] = {}

        for t2unit in self.t2info_from:
            t2_result = tran_view.get_t2_result(unit_id=t2unit)
            if t2_result is not None:
               info[t2unit] = t2_result
        return info




    def add(self, transients) -> Dict[StockId, JournalTweak]:
        """
        Loop through transients and check for TNS names and/or candidates to submit.
        Outputs to be stored in the transient Journal is recorded as JournalTweaks (dicts)
        in the return dict.
        """

        journal_updates = {}
        # Iterate through transients received by this unit. 
        # Information is contained in a SnapView object, which provides a snapshot of all data available to
        # a user at a given time. 
        for tv in transients:

            transientinfo = self.collect_info(tv)
            self.logger.info("Recieved", extra={"tranId": tv.id})

            # A reaction method is executed for each transient
            success, jcontent = self.react(tv, transientinfo)
                
            if jcontent is not None:
                jup = JournalTweak(extra=jcontent)
                journal_updates[tv.id] = jup


        return journal_updates

    def done(self):
        """ """
        # Should possibly do some accounting or verification
        self.logger.info("T3HelloWorld out")
