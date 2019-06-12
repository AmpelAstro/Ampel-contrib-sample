from setuptools import setup
setup(name='Ampel-contrib-sample',
      version='0.5.0',
      package_data = {'': ['*.json']},
      packages=[
          'ampel.contrib.groupname',
          'ampel.contrib.groupname.t0',
          'ampel.contrib.groupname.t2',
      ],
      entry_points = {
          'ampel.channels' : [
              'groupname = ampel.contrib.groupname.channels:load_channels',
          ],
          'ampel.pipeline.t0.units' : [
              'DecentFilterCopy = ampel.contrib.groupname.t0.DecentFilterCopy:DecentFilterCopy',
              'ExampleFilter = ampel.contrib.groupname.t0.ExampleFilter:ExampleFilter',
              'SampleFilter = ampel.contrib.groupname.t0.SampleFilter:SampleFilter',
          ],
          'ampel.pipeline.t2.units' : [
              'POLYFIT = ampel.contrib.groupname.t2.T2ExamplePolyFit:T2ExamplePolyFit'
          ],
          'ampel.pipeline.t2.configs' : [
              'groupname = ampel.contrib.groupname.channels:load_t2_run_configs',
          ],
          'ampel.pipeline.t3.jobs' : [
              'groupname = ampel.contrib.groupname.channels:load_t3_jobs',
          ],
      }
)