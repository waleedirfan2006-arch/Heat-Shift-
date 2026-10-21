.PHONY: data hourly
PYTHON ?= python

data:
	$(PYTHON) HeatShift_Warehouse/pipeline.py --output "$(if $(WORKDIR),$(WORKDIR),automation/runs/historical)"
hourly:
	$(PYTHON) automation/hourly_pipeline.py --output "$(if $(WORKDIR),$(WORKDIR),automation/runs/live)"
