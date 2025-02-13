PYTHON := python3

DESIGN_DIR := ../../
AST_XML := $(DESIGN_DIR)/ast/Vpicorv32_axi.xml
AST_XML_flat := $(DESIGN_DIR)/ast/Vpicorv32_axi_flat.xml


rtl:
	cd $(DESIGN_DIR) && cp rtl/picorv32_modified.v picorv32.v && cp rtl/testbench_modified.v testbench.v

$(AST_XML): xml.vc
	cd $(DESIGN_DIR) && cp rtl/picorv32_modified.v picorv32.v && cp rtl/testbench_modified.v testbench.v
	cd $(DESIGN_DIR) && verilator -f xml.vc

$(AST_XML_flat): xml_flat.vc
	cd $(DESIGN_DIR) && cp rtl/picorv32_modified.v picorv32.v && cp rtl/testbench_modified.v testbench.v
	cd $(DESIGN_DIR) && verilator -f xml_flat.vc

check: ast_checker.py ast_analyzer.py $(AST_XML)
	$(PYTHON) ast_checker.py -f $(AST_XML)

check_flat: ast_checker.py $(AST_XML_flat)
	$(PYTHON) ast_checker.py -f $(AST_XML_flat)

analyze: ast_analyzer.py
	$(PYTHON) ast_analyzer.py -f $(AST_XML_flat)

schedule: check
	$(PYTHON) ast_schedule.py -f $(AST_XML_flat)

preprocess: check
	$(PYTHON) ast_sim_prepare.py -f $(AST_XML_flat)

sim: check ast_schedule.py
	$(PYTHON) ast_simulator.py -f $(AST_XML_flat)

fsim: check ast_schedule.py
	$(PYTHON) ast_fsimulator.py -f $(AST_XML_flat)

gen_pysim_wrap: sig_list/pysim_sig_table.json 
	$(PYTHON) gen_pysim_wrapper.py

gen_ff_wrap: sig_list/fsim_sig_table.json 
	$(PYTHON) gen_ff_wrapper.py

gen_fi_wrap: sig_list/fsim_sig_table.json 
	$(PYTHON) gen_fi_wrapper.py
