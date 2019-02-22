# Alert Management, Photometry and Evaluation of Lightcurves (AMPEL)


Alert Management, Photometry and Evaluation of Lightcurves (**AMPEL**) is a modular software framework designed for the analysis of streamed data. AMPEL operates in four different tiers: 

- T0 filters alerts from a stream 
- T1 looks for new transient data to add from outside the stream 
- T2 calculates/derives further properties based on the collected information
- T3 triggers reactions

Users are free to add their own operational *units*, implemented as python modules, to each tier of the live AMPEL system.  *Channels* request the use of units. This provides great power and freedom in that (almost) any combination of algorithms can be implemented and used for complete, repeatable scientific studies. However, it carries an initial cost in that units and channels have to be preconfigured. This repository contains a development version of AMPEL that allows channels and units to be developed and tested on static alert collections. Modules developed using these tools can later be merged into a full AMPEL instance where they are applied either to live alert streams or archived data. Instructions for how to install the development kit and how to design AMPEL units can be found in the [notebooks directory](notebooks/) of this repository. The rest of this README contains a general introduction to the AMPEL system.


## Introduction

Both multi-messenger astronomy and new high-throughput wide-field surveys require the development of flexible tools for the selection and analysis of astrophysical transients. The Alert Management, Photometry and Evaluation of Lightcurves (AMPEL) system is a streaming data analysis framework. As such it functions to accept, process and react to streams of transient data. AMPEL contains a broker as the first of four pipeline levels, or 'tiers', where each can incoroporate user-contributed analysis units. These tools are embedded into a framework that encourages provenance and keeps track of the varying information states that a transient displays. The latter concept includes information gathered over time, but also tracks varying data access levels and e.g. improved calibration. AMPEL provides a tool that can assist in filtering transients in real time, running realistic alert reaction simulations, reprocessing of full datasets as well as the final scientific analysis of transient data.

 AMPEL differs from most other brokers in the focus on the full analysis chain of streamed data. As a consequence, there is no (curated) collection to be queried after alerts have been received. AMPEL users are rather pro-active in designing channels which are merged into the live instance and exposed to the full stream. This carries an initial cost in terms of channel creation based on archive data but provides full flexibility in analysis design, provenance and what reactions are possible.

The live AMPEL instance functions as a public broker for use with the public ZTF alert stream. Contact the administators to set up your channel based on this repository.


## AMPEL in a nutshell

The core object in AMPEL is a *transient*, a single object identified by a creation date and typically a region of origin in the sky. Each transient is linked to a set of *datapoints* that represent individual measurements. Datapoints can be added, updated, marked as bad, or replaced, but never removed. Each datapoint can be associated with tags indicating e.g. any masking or proprietary restrictions. Transients and datapoints are connected by *states*, where a state references a *compound* of datapoints. A state represents a view of a transient available at some time and for some observer. For an optical photometric survey, a compound can be directly interpreted as a set of flux measurements or a lightcurve.

> Example: A ZTF alert corresponds to a potential transient. Datapoints here are simply the photometric magnitudes reported by ZTF. When first inserted, a transient has a single state with a compound consisting of the datapoints in the initial alert. If this transient is detected again, the new datapoint is added to the collection and a new state created containing both previous and new data. Should the first datapoint be public but the second datapoint be private, only users with proper access will see the updated state. 

Using AMPEL means creating a *channel*, corresponding to a specific science goal, which prescribes behavior at four different stages, or *tiers*. What tasks should be performed at what tier can be determined by answers to the questions: *Tier 0: What are the minimal requirements for an alert to be interesting?*, *Tier 1:  Can datapoints be changed by events external to the stream?*, *Tier 2:  What calculations should be done on each of the candidates states?*, *Tier 3: What operations should be done at timed intervals?*

In Tier 0 (T0), the full alert stream is *filtered* to only include potentially interesting candidates. This tier thus works as a data broker: objects that merit further study are selected from the incoming alert stream. However, unlike most brokers, accepted transients are inserted into a database (DB) of active transients rather than immediately being sent downstream. Users can either provide their own algorithm for filtering, or configure one of the filter classes provided by the community, according to their needs. 


> Example T0: The simple AMPEL channel `BrightNStable` looks for variables with at least three well behaved detections (few bad pixels and reasonable subtraction FWHM) and not coincident with a Gaia DR2 star-like source. This is implemented through a python class SampleFilter that operates on an alert and returns either a list of requests for follow-up (T2) analysis, if selection criteria are fulfilled, or `False` if they are not. AMPEL will test every ZTF alert using this class, and all alerts that pass the cut are added to the active transient DB. The transient is then associated with the channel ``BrightNStable''. 


Tier 1 (T1) is largely autonomous and exists in parallel to the other tiers. T1 carries out duties related to *updates* of datapoints and states. Example activities include completing transient states with datapoints that were present in new alerts but where these were not individually accepted by the channel filter (e.g., in the case of lower significance detections at late phases), as well as querying an external archive for updated calibration or adding photometry from additional sources.


Additional transient information is derived or retrieved in Tier 2 (T2), and are always connected to a state and stored as a *ScienceRecord*. T2 units either work with the empty state, relevant for e.g. catalog matching that only depends on the position, or depends on the datapoints of a state to calculate new, derived transient properties. In the latter case, the T2 task will be called again as soon as a new state is created.  This could be due both to new observations or, for example, updated calibration of old datapoints. Possible T2 units include lightcurve fitting, photometric redshift estimation, machine learning classification, and catalog matching.

> Example T2: For an optical transient, a state corresponds to a lightcurve and each photometric observation is represented by a datapoint. A new observation of the transient would extend the lightcurve and thus create a new state. `BrightNStable` requests a third order polynomial fit  for each state  using the `T2PolyFit` class. The outcome, in this case polynomial coefficients, are saved to the database.


The final AMPEL level, Tier 3 (T3), consists of *schedulable* actions. While T2s are initiated by events (the addition of new states), T3 units are executed at pre-determined times. These can range from yearly data dumps, to daily updates, to effectively real-time execution every few seconds. T3 processes access data through the *TransientView*, which concatenates all  information regarding a transient. This includes both states and ScienceRecords that are accessible by the channel. T3s iterate through all transients of a channel. This allows for an evaluation of multiple ScienceRecords, and comparisons between different objects or, more generally, any kind of population analysis. One typical case is the ranking of candidates which would be interesting to observe on a given night.  T3 units include options to push and pull information from for example Slack, TNS and web-servers.

> Example T3: The science goal of ``BrightNStable'' is to observe transients with a steady rise. At the T3 stage the channel therefore loops through the TransientViews, and examines all T2PolyFit science records for fit parameters which indicate a lasting linear rise. Any transients fulfilling the final criteria trigger an immediate notification sent to the user. This test is scheduled to be performed at 13:15 UT each day.              


## Life of a transient in AMPEL

![TransientLife](figures/ampellife.png)


*Life of a transient in AMPEL*. Sample behaviour at the four tiers of AMPEL as well as the database access are shown as columns, with the left side of the figure indicating when the four alerts belonging to the transient were received.
1. T0: The first alert is rejected as being too faint, while the following passes the channel acceptance critiera. The third alert is rejected due to unexpected color. 
2. T1: Photometric information is added outside of the filter at three ocations. Firstly, new observations of channel transients are added even if alerts in isolation would not be accepted. Seccondly, an observation from another facility is added. Thirdly,  updated calibration of a measurement cause this datapoint to be replaced.
3. T2: Every time a new state is created a lightcurve fit is performed and the fit results stored as a Science Records.
4. T3: A unit regularly tests whether the transient warrants a Slack posting (requesting potential further follow-up). The submit criteria are fulfilled the second time the unit is run. In both cases the evaluation is stored in the transient *Journal*, which is later used to prevent a transient to be posted multiple times. Once the transient has been not been updated for an extended time a T3 unit *purges* the transient to an external database that can be direclty queried by channel owners.
5. Database: A transient entry is created in the DB as the first alert is accepted. After this, each new datapoint causes a new state to be created. T2 Science Records are each associated with one state. The T3 units return information that is stored in the Journal.

A technical outline of AMPEL can be found [here](figures/ZTF_Pipeline_overview_June_18.pdf).





## How to use this repository to create a full AMPEL channel

Incorporating modules and channels into a live instance briefly consists of: i. Forking this repository under a name *Ampel-contrib-xyz* where xyz is a unique name ii. Add new units to the t0/t2/t3 subdirectories. iii. Define a channel to use this using the base configuration files. iv. Use the dev alert processor and notebooks to verify expected behaviour. v. Discuss with AMPEL administrators to queue repository for inclusion into the the next build.

### Creating units for the T0 and T2 tiers

Units that are to be run through AMPEL should be included in the correct folder of the [ampel/contrib/groupname/](ampel/contrib/groupname/) as a python module inheriting from an appropriate abstract class. Examples of this process exists in this repository and the base definitions can be found in [Ampel-base](https://github.com/AmpelProject/Ampel-base). Use notebooks similar to those shown  [here](notebooks/) to develop and test these.

> There are currently no sample units for the T1 and T3 stages. Contact the admininstrators for assistance in developing these.

### Configuration files

Each channel is defined in a configuration file similar to [this](ampel/contrib/groupname/channels.json). These describe which units each channel should make use of and the *run parameters* that should be provided to the unit when executed.



## The AMPEL live instance: parsing the ZTF alert stream and submitting candidates to TNS 

An instance of AMPEL hosted at the DESY computer centre (Zeuthen) recieves and parses the live ZTF alert stream distributed by the University of Washingtion. This process is summarized in the following figure:

![AmpelLive](figures/ampel_intro.png)

One of the channels in this instance is being tuned to automatically submit high-quality extragalactic candidates with a high probability of being supernovae or AGNs to the TNS. The current selection focuses on transients brighter than 19.5 mag and with a contamination by stellar variability at <5%. Submission can be found at the TNS with the sender *AMPEL_ZTF_MSIP*. 

## 
