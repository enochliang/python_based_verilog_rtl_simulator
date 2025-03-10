import os
from config import *


class GenMakefile:
    def __init__(self, design_name:str, pysim_mode:str="full", fsim_mode:str="full", start_cyc=None, period=None):
        config = configs[design_name]

        self.python_cmd = config["python_cmd"]
        self.design_folder = config["design_folder"]
        self.tb_clk = config["tb_clk"]
        self.tb_rst = config["tb_rst"]
        self.hier_above_top = config["top_hier"]
        self.min_cyc = config["min_cyc"]
        self.max_cyc = config["max_cyc"]

        #self.design_folder = os.path.abspath(design_dir)
        self.top_module_name = config["top_module_name"]

        self.makefile_path = "./Makefile"
        ast_folder = "ast"
        sig_list_folder = "sig_list"

        self.hw_root = "../hardware"
        self.design_dir = os.path.abspath(self.hw_root) + "/" + self.design_folder

        # verilator argument file for ast generation
        self.ast_vc      = "ast.vc"
        self.ast_flat_vc = "ast_flat.vc"

        # ast xml file name with absolute directory
        self.ast_dir  = self.design_dir + "/" + ast_folder
        self.ast      = self.ast_dir + "/V" + self.top_module_name + ".xml"
        self.ast_flat = self.ast_dir + "/V" + self.top_module_name + "_flat.xml"

        # signal table folder absolute directory
        self.sig_list_dir = self.design_dir + "/" + sig_list_folder

        self.LOG_VAL_DIR    = self.design_dir + "/pysim_ff_value"
        self.FF_VAL_DIR     = self.design_dir + "/ff_value"
        self.GOLDEN_VAL_DIR = self.design_dir + "/golden_value"
        self.RESULT_DIR     = self.design_dir + "/result"

        if start_cyc:
            self.start_cyc = start_cyc
        if period:
            self.period = period
        self.pysim_mode = pysim_mode
        self.fsim_mode = fsim_mode

        self.makefile = ""


    def _gen_define(self):
        self.makefile += "PYTHON := " + self.python_cmd + "\n\n"
        self.makefile += "# design repo directory\n"
        self.makefile += "DESIGN_DIR := " + self.design_dir + "\n\n"
        self.makefile += "# top module name\n"
        self.makefile += "TOP_MODULE_NAME := " + self.top_module_name + "\n\n"
        self.makefile += "# ast directory\n"
        self.makefile += "AST_XML := " + self.ast + "\n"
        self.makefile += "AST_XML_flat := " + self.ast_flat + "\n\n"
        self.makefile += "# sig_list directory\n"
        self.makefile += "SIG_DIR := " + self.sig_list_dir + "\n\n"
        self.makefile += "# dumped logic value directory\n"
        self.makefile += "LOG_VAL_DIR := " + self.LOG_VAL_DIR + "\n\n"
        #self.makefile += "# design variable\n"
        #self.makefile += "tb_clk := " + self.tb_clk + "\n"
        #self.makefile += "tb_rst := " + self.tb_rst + "\n"
        #self.makefile += "hier_above_top := " + self.hier_above_top + "\n"

    def _gen_ast(self):
        self.makefile += "#=============================\n"
        self.makefile += "# AST Generation              \n"
        self.makefile += "#=============================\n"
        self.makefile += "$(AST_XML):\n"
        self.makefile += f"\tmkdir -p {self.ast_dir}\n"
        self.makefile += "\tcd $(DESIGN_DIR) && verilator -f " + self.ast_vc + "\n\n"
        self.makefile += "$(AST_XML_flat):\n"
        self.makefile += f"\tmkdir -p {self.ast_dir}\n"
        self.makefile += "\tcd $(DESIGN_DIR) && verilator -f " + self.ast_flat_vc + "\n\n"

    def _gen_check(self):
        self.makefile += "#=============================\n"
        self.makefile += "# Checking                    \n"
        self.makefile += "#=============================\n"
        self.makefile += "check: ast_checker.py ast_analyzer.py $(AST_XML)\n"
        self.makefile += "\t$(PYTHON) ast_checker.py -f $(AST_XML)\n\n"
        self.makefile += "check_flat: ast_checker.py $(AST_XML_flat)\n"
        self.makefile += "\t$(PYTHON) ast_checker.py -f $(AST_XML_flat)\n"

    def _gen_sig_table(self):
        self.makefile += "#=============================\n"
        self.makefile += "# Signal Table Generation     \n"
        self.makefile += "#=============================\n"
        self.makefile += "sig_table: \n"
        self.makefile += "\tmkdir -p $(SIG_DIR)\n"
        self.makefile += f"\t$(PYTHON) sig_table_prepare.py -f $(AST_XML_flat) -l $(SIG_DIR) --design_dir {self.design_dir}\n\n"

    def _gen_preprocess(self):
        self.makefile += "#=============================\n"
        self.makefile += "# Preprocess                  \n"
        self.makefile += "#=============================\n"
        self.makefile += "preprocess: check \n"
        self.makefile += f"\t$(PYTHON) ast_sim_prepare.py -f $(AST_XML_flat) --logic_value_dir {self.LOG_VAL_DIR} --sig_list_dir $(SIG_DIR) --design_dir {self.design_dir}\n\n"

        self.makefile += "prepare_fsim_folder:\n"
        self.makefile += f"\tmkdir -p {self.design_dir}/result\n"
        self.makefile += f"\tmkdir -p {self.design_dir}/ff_value\n"
        self.makefile += f"\tmkdir -p {self.design_dir}/golden_value\n\n"
        self.makefile += "prepare_pysim_folder:\n"
        self.makefile += f"\tmkdir -p {self.design_dir}/pysim_ff_value\n\n"

        self.makefile += "clear_fsim_folder:\n"
        self.makefile += f"\trm -rf {self.design_dir}/result\n"
        self.makefile += f"\trm -rf {self.design_dir}/ff_value\n"
        self.makefile += f"\trm -rf {self.design_dir}/golden_value\n\n"
        self.makefile += "clear_pysim_folder:\n"
        self.makefile += f"\trm -rf {self.design_dir}/pysim_ff_value\n\n"
        
        self.makefile += "gen_pysim_wrap: " + self.sig_list_dir + "/pysim_sig_table.json \n"
        self.makefile += f"\t$(PYTHON) gen_pysim_wrapper.py --tb_clk {self.tb_clk} --tb_rst {self.tb_rst} --top_module_name {self.top_module_name} --hier_above_top {self.hier_above_top} --ff_value_dir {self.LOG_VAL_DIR } --sig_list_dir {self.sig_list_dir}\n\n"
        self.makefile += "gen_ff_wrap: " + self.sig_list_dir + "/fsim_sig_table.json \n"
        self.makefile += f"\t$(PYTHON) gen_ff_wrapper.py --tb_clk {self.tb_clk} --tb_rst {self.tb_rst} --top_module_name {self.top_module_name} --hier_above_top {self.hier_above_top} --ff_value_dir {self.FF_VAL_DIR} --sig_list_dir {self.sig_list_dir} --golden_value_dir {self.GOLDEN_VAL_DIR}\n\n"
        self.makefile += "gen_fi_wrap: " + self.sig_list_dir + "/fsim_sig_table.json \n"
        self.makefile += f"\t$(PYTHON) gen_fi_wrapper.py --tb_clk {self.tb_clk} --tb_rst {self.tb_rst} --top_module_name {self.top_module_name} --hier_above_top {self.hier_above_top} --ff_value_dir {self.FF_VAL_DIR} --sig_list_dir {self.sig_list_dir} --golden_value_dir {self.GOLDEN_VAL_DIR} --result_dir {self.RESULT_DIR}\n\n"

    def _gen_pysim(self):
        self.makefile += "#=============================\n"
        self.makefile += "# Py-simulation               \n"
        self.makefile += "#=============================\n"
        self.makefile += "pyfsim: check ast_schedule.py \n"
        self.makefile += f"\t$(PYTHON) ast_fsimulator.py -f $(AST_XML_flat) -l $(LOG_VAL_DIR) --logic_value_dir {self.LOG_VAL_DIR} --sig_list_dir $(SIG_DIR) --start_cyc {self.start_cyc} --min_cyc {self.min_cyc} --max_cyc {self.max_cyc} --period {self.period} --design_dir {self.design_dir} --mode {self.pysim_mode}\n\n"

    def _gen_fsim(self):
        self.makefile += "#=============================\n"
        self.makefile += "# Fault injection             \n"
        self.makefile += "#=============================\n"
        self.makefile += "fsim: fi_controller.py \n"
        self.makefile += f"\t$(PYTHON) fi_controller.py -m '{self.fsim_mode}' -t {self.design_dir}/prob_rw_table_{self.start_cyc}-{self.start_cyc+self.period-1}.csv -d {self.design_dir} -f 'cd {self.design_dir} && ./fi_sim_veri' -s {self.design_dir}/sig_list/fsim_sig_table.json\n\n"

    def _gen_ace_analysis(self):
        self.makefile += "#=============================\n"
        self.makefile += "# Ace Analysis                \n"
        self.makefile += "#=============================\n"
        self.makefile += "ace: \n"
        self.makefile += f"\t$(PYTHON) ace_analysis.py --rw_table_dir {self.design_dir}/prob_rw_table_{self.start_cyc}-{self.start_cyc+self.period-1}.csv --sig_list_dir {self.design_dir}/sig_list/fsim_sig_table.json\n"

    def generate(self):
        self._gen_define()
        self._gen_ast()
        self._gen_check()
        self._gen_sig_table()
        self._gen_preprocess()
        self._gen_pysim()
        self._gen_fsim()
        self._gen_ace_analysis()
        print(self.makefile)


if __name__ == "__main__":

    gen = GenMakefile(
            design_name="sha1", 
            start_cyc=5, 
            period=239,
            pysim_mode="period",
            fsim_mode="data"
            )
    #gen = GenMakefile(
    #        design_name="picorv32_firmware", 
    #        start_cyc=300000, 
    #        period=2048,
    #        pysim_mode="period",
    #        fsim_mode="data"
    #        )
    
    #gen = GenMakefile("python3", "../Tinyriscv", "tinyriscv", "clk", "rst", "tinyriscv_soc_tb.tinyriscv_soc_top_0.u_tinyriscv")
    gen.generate()


