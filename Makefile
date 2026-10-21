.PHONY: data hourly
PYTHON ?= python
WORKDIR ?= automation/runs/historical

data:
	$(PYTHON) HeatShift_Warehouse/pipeline.py $(if $(WORKDIR),--output "$(WORKDIR)",)
hourly:
	$(PYTHON) automation/hourly_pipeline.py $(if $(WORKDIR),--output "$(WORKDIR)",)
