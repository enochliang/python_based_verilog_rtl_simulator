PYTHON := python3

# design repo directory
DESIGN_DIR := ../picorv32

# top module name
TOP_MODULE_NAME := picorv32_axi

# ast directory
AST_XML := $(DESIGN_DIR)/ast/V$(TOP_MODULE_NAME).xml
AST_XML_flat := $(DESIGN_DIR)/ast/V$(TOP_MODULE_NAME)_flat.xml

# dumped logic value directory
LOG_VAL_DIR := $(DESIGN_DIR)/pysim_ff_value/

#=============================
# AST Generation
#=============================
$(AST_XML):
	cd $(DESIGN_DIR) && make ast

$(AST_XML_flat):
	cd $(DESIGN_DIR) && make ast_flatten

#=============================
# Checking
#=============================
check: ast_checker.py ast_analyzer.py $(AST_XML)
	$(PYTHON) ast_checker.py -f $(AST_XML)

check_flat: ast_checker.py $(AST_XML_flat)
	$(PYTHON) ast_checker.py -f $(AST_XML_flat)

#======================================
# Preprocess & Signal Table Generation
#======================================
preprocess: check
	mkdir -p sig_list
	$(PYTHON) ast_sim_prepare.py -f $(AST_XML_flat)

sig_table:
	mkdir -p sig_list
	$(PYTHON) sig_table_prepare.py -f $(AST_XML_flat)

gen_pysim_wrap: sig_list/pysim_sig_table.json 
	$(PYTHON) gen_pysim_wrapper.py

gen_ff_wrap: sig_list/fsim_sig_table.json 
	$(PYTHON) gen_ff_wrapper.py

gen_fi_wrap: sig_list/fsim_sig_table.json 
	$(PYTHON) gen_fi_wrapper.py

#========================
# Py-simulation
#========================
sim: check ast_schedule.py
	$(PYTHON) ast_simulator.py -f $(AST_XML_flat)

fsim: check ast_schedule.py
	$(PYTHON) ast_fsimulator.py -f $(AST_XML_flat) -l $(LOG_VAL_DIR)


#analyze: ast_analyzer.py
#	$(PYTHON) ast_analyzer.py -f $(AST_XML_flat)
#schedule: check
#	$(PYTHON) ast_schedule.py -f $(AST_XML_flat)
