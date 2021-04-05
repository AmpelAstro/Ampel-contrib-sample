from os.path import dirname, join
import json

def load_channels():
	with open(join(dirname(__file__), "channels.json")) as f:
		return json.load(f)

def load_t2_run_configs():
	with open(join(dirname(__file__), "t2_run_configs.json")) as f:
		return json.load(f)

def load_t3_jobs():
	with open(join(dirname(__file__), "t3_jobs.json")) as f:
		return json.load(f)