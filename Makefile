PYTHON := python3

DESIGN_DIR := ../picorv32
AST_XML := $(DESIGN_DIR)/ast/Vpicorv32_axi.xml


$(AST_XML): $(DESIGN_DIR)/*.v
	cd $(DESIGN_DIR) && verilator -f xml.vc

check: ast_checker.py ast_analyzer.py $(AST_XML)
	$(PYTHON) ast_checker.py -f $(AST_XML)

analyze: ast_analyzer.py
	$(PYTHON) ast_analyzer.py -f $(AST_XML)

schedule: check ast_schedule.py
	$(PYTHON) ast_schedule.py -f $(AST_XML)

sim: check ast_schedule.py
	$(PYTHON) ast_simulator.py -f $(AST_XML)

fsim: check ast_schedule.py
	$(PYTHON) ast_fsimulator.py -f $(AST_XML)

gen_fi_wrapper: sig_list/simulator_sig_dict.json 
	$(PYTHON) ast_.py
