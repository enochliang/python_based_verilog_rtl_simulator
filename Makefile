PYTHON := python3

DESIGN_DIR := ../../ #(changable)
AST_XML := $(DESIGN_DIR)/ast/Vpicorv32_axi.xml
AST_XML_flat := $(DESIGN_DIR)/ast/Vpicorv32_axi_flat.xml

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
	$(PYTHON) ast_sim_prepare.py -f $(AST_XML_flat)

sig_list/pysim_sig_table.json:
	make preprocess

sig_list/fsim_sig_table.json:
	make preprocess

sig_list/fsim_sig_table.json:
	make preprocess

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
	$(PYTHON) ast_fsimulator.py -f $(AST_XML_flat)


#analyze: ast_analyzer.py
#	$(PYTHON) ast_analyzer.py -f $(AST_XML_flat)
#schedule: check
#	$(PYTHON) ast_schedule.py -f $(AST_XML_flat)
