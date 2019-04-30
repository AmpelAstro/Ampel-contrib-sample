# Ampel-contrib-sample Notebooks

These notebooks contain examples of how to get to know, implement and test units for the **AMPEL** tiers in a standalone way. Standalone means that the fairly complex background database and its task managers do not need to be installed and initiated. The AMPEL development packages are constructed such that units (python modules) that run with these will also function in the full, online AMPEL and system.

The `t0_unit_example` jupyter notebook provides an first introduction both to the **AMPEL** development system as well as T0 filter units. The `t0_advanced_example` further explores the creation of filter units and `t2_unit_examples` introduces T2 classes.

T3 units are harder to construct since they make use of further concepts such as TransientViews and the Journal, and iterate over chunks of all transients saved by the channel. We recommend channels to start by using the preconfigured units provided by the AMPEL development teams.

For futher guidance on the implementation of **AMPEL** channels, contact ampel-info at desy.de.

## Installation with Pip

### Requirements

AMPEL requires python 3.6+ and

* [Git](https://git-scm.com/downloads)
* [Python Pip](https://pip.pypa.io/en/stable/installing/)
* [VirtualEnv](https://virtualenv.pypa.io/en/latest/installation/) (optional)

### Instructions

In order to edit and run the example notebooks you must first clone the `Ampel-contrib-sample` repository:

```
git clone https://github.com/AmpelProject/Ampel-contrib-sample.git
```

Then, you must install the code inside this repository. The easiest way to do this is by using the developer mode of the `pip` command (we recommend using this inside a [virtual environment](https://virtualenv.pypa.io/en/latest/)):

```
pip install -e Ampel-contrib-sample/
```

Afterwards, proceed to install the rest of the dependencies via pip using the `requirements.txt` file included in the `Ampel-contrib-sample` repository:

```
pip install -r Ampel-contrib-sample/requirements.txt
```

Note that this will install two other AMPEL repositories: Ampel-base (containing class definitions) and Ampel-base-ZTF (which contains the shaper classes that can ingest ZTF alerts).

Finally, just run the command:

```
jupyter notebook
```

and then, in the browser webpage that is going to open automatically, access the `Ampel-contrib-sample/notebooks/` directory where the notebooks are located, and click on the notebook you want to run. For more information on how to run Jupyter notebooks, please see https://jupyter-notebook.readthedocs.io/en/stable/

## Installation with conda

TBA
