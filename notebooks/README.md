# Ampel-contrib-sample Notebooks

These notebooks contain examples of how to implement and run units for each one of the AMPEL tiers in a standalone way. This is, without the need to have the whole AMPEL system, with all of its services, running.

## Installation with Pip

### Requirements

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

Finally, just run the command:

```
jupyter notebook
```

and then, in the browser webpage that is going to open automatically, access the `Ampel-contrib-sample/notebooks/` directory where the notebooks are located, and click on the notebook you want to run. For more information on how to run Jupyter notebooks, please see https://jupyter-notebook.readthedocs.io/en/stable/

## Installation with conda

TBA