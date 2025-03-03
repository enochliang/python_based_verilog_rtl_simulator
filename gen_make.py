import os

config = {
        "picorv32":{
            "tool":"python3",
            "design_dir":"/ibex/hardware/picorv32/benchmark_basicmath/",
            "top_module_name":"picorv32",
            "tb_clk":"clk",
            "tb_rst":"rst",
            "hier_above_top":"top.uut",
            "ast_folder":"ast",
            "ast_vc":"AST.vc",
            "ast_flat_vc":"AST_flat.vc",
            "start_cyc":5,
            "min_cyc":0,
            "max_cyc":5,
            "period":8
        },


    }

class GenMakefile:
    def __init__(self, tool, design_dir, top_module_name, tb_clk, tb_rst, hier_above_top, ast_folder, AST, AST_flat, start_cyc=0, min_cyc=0, max_cyc=0):
        self.tool = tool
        self.design_dir = os.path.abspath(design_dir)
        self.top_module_name = top_module_name
        self.makefile_path = "./Makefile"
        self.ast      = self.design_dir + "/" + ast_folder + "/V" + top_module_name + ".xml"
        self.ast_flat = self.design_dir + "/" + ast_folder + "/V" + top_module_name + "_flat.xml"
        self.sig_list_dir = self.design_dir + "/sig_list"
        self.LOG_VAL_DIR = self.design_dir + "/pysim_ff_value"
        self.FF_VAL_DIR = self.design_dir + "/ff_value"
        self.GOLDEN_VAL_DIR = self.design_dir + "/golden_value"
        self.RESULT_DIR = self.design_dir + "/result"
        self.makefile = ""
        self.AST = AST
        self.AST_flat = AST_flat
        self.tb_clk = tb_clk
        self.tb_rst = tb_rst
        self.hier_above_top = hier_above_top
        self.start_cyc = start_cyc
        self.min_cyc = min_cyc
        self.max_cyc = max_cyc

    def _gen_define(self):
        self.makefile += "PYTHON := " + self.tool + "\n\n"
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
        self.makefile += "\tcd $(DESIGN_DIR) && "
        self.makefile += "verilator -f " + self.AST + "\n\n"
        self.makefile += "$(AST_XML_flat):\n"
        self.makefile += "\tcd $(DESIGN_DIR) && "
        self.makefile += "verilator -f " + self.AST_flat + "\n\n"

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
        self.makefile += "\t$(PYTHON) sig_table_prepare.py -f $(AST_XML_flat) -l $(SIG_DIR)\n\n"

    def _gen_preprocess(self):
        self.makefile += "#=============================\n"
        self.makefile += "# Preprocess                  \n"
        self.makefile += "#=============================\n"
        self.makefile += "preprocess: check \n"
        self.makefile += f"\t$(PYTHON) ast_sim_prepare.py -f $(AST_XML_flat) --logic_value_dir {self.LOG_VAL_DIR} --sig_list_dir $(SIG_DIR)\n\n"
        self.makefile += "gen_pysim_wrap: " + self.sig_list_dir + "/pysim_sig_table.json \n"
        self.makefile += f"\tmkdir -p {self.design_dir}/pysim_ff_value\n"
        self.makefile += f"\tmkdir -p {self.design_dir}/ff_value\n"
        self.makefile += f"\tmkdir -p {self.design_dir}/golden_value\n"
        self.makefile += f"\t$(PYTHON) gen_pysim_wrapper.py --tb_clk {self.tb_clk} --tb_rst {self.tb_rst} --top_module_name {self.top_module_name} --hier_above_top {self.hier_above_top} --ff_value_dir {self.LOG_VAL_DIR } --sig_list_dir {self.sig_list_dir}\n\n"
        self.makefile += "gen_ff_wrap: " + self.sig_list_dir + "/fsim_sig_table.json \n"
        self.makefile += f"\tmkdir -p {self.design_dir}/pysim_ff_value\n"
        self.makefile += f"\tmkdir -p {self.design_dir}/ff_value\n"
        self.makefile += f"\tmkdir -p {self.design_dir}/golden_value\n"
        self.makefile += f"\t$(PYTHON) gen_ff_wrapper.py --tb_clk {self.tb_clk} --tb_rst {self.tb_rst} --top_module_name {self.top_module_name} --hier_above_top {self.hier_above_top} --ff_value_dir {self.FF_VAL_DIR} --sig_list_dir {self.sig_list_dir} --golden_value_dir {self.GOLDEN_VAL_DIR}\n\n"
        self.makefile += "gen_fi_wrap: " + self.sig_list_dir + "/fsim_sig_table.json \n"
        self.makefile += f"\tmkdir -p {self.design_dir}/pysim_ff_value\n"
        self.makefile += f"\tmkdir -p {self.design_dir}/ff_value\n"
        self.makefile += f"\tmkdir -p {self.design_dir}/golden_value\n"
        self.makefile += f"\t$(PYTHON) gen_fi_wrapper.py --tb_clk {self.tb_clk} --tb_rst {self.tb_rst} --top_module_name {self.top_module_name} --hier_above_top {self.hier_above_top} --ff_value_dir {self.FF_VAL_DIR} --sig_list_dir {self.sig_list_dir} --golden_value_dir {self.GOLDEN_VAL_DIR} --result_dir {self.RESULT_DIR}\n\n"

    def _gen_pysim(self):
        self.makefile += "#=============================\n"
        self.makefile += "# Py-simulation               \n"
        self.makefile += "#=============================\n"
        self.makefile += "fsim: check ast_schedule.py \n"
        self.makefile += f"\t$(PYTHON) ast_fsimulator.py -f $(AST_XML_flat) -l $(LOG_VAL_DIR) --logic_value_dir {self.LOG_VAL_DIR} --sig_list_dir $(SIG_DIR) --start_cyc {self.start_cyc} --min_cyc {self.min_cyc} --max_cyc {self.max_cyc}\n\n"


    def generate(self):
        self._gen_define()
        self._gen_ast()
        self._gen_check()
        self._gen_sig_table()
        self._gen_preprocess()
        self._gen_pysim()
        print(self.makefile)


if __name__ == "__main__":

    #TODO
    #tool = "python3"
    #design_dir = "../Tinyriscv"
    #top_module_name = "tinyriscv"
    #tb_clk = "clk"
    #tb_rst = "rst"
    #hier_above_top = "tinyriscv_soc_tb.tinyriscv_soc_top_0.u_tinyriscv"
    #AST = "AST.vc"
    #AST_flat = "AST_flat.vc"
    #start_cyc = 800
    #min_cyc = 800
    #max_cyc = 900

    #gen = GenMakefile(tool, design_dir, top_module_name, tb_clk, tb_rst, hier_above_top, AST, AST_flat, start_cyc, min_cyc, max_cyc)
    #
    #    #gen = GenMakefile("python3", "../Tinyriscv", "tinyriscv", "clk", "rst", "tinyriscv_soc_tb.tinyriscv_soc_top_0.u_tinyriscv")
    #gen.generate()
    design = "picorv32"
    tool = config[design]["tool"]
    design_dir = config[design]["design_dir"]
    top_module_name = config[design]["top_module_name"]
    tb_clk = config[design]["tb_clk"]
    tb_rst = config[design]["tb_rst"]
    hier_above_top = config[design]["hier_above_top"]
    ast_folder = config[design]["ast_folder"]
    AST = config[design]["ast_vc"]
    AST_flat = config[design]["ast_flat_vc"]
    start_cyc = config[design]["start_cyc"]
    min_cyc = config[design]["min_cyc"]
    max_cyc = config[design]["max_cyc"]

    gen = GenMakefile(tool, design_dir, top_module_name, tb_clk, tb_rst, hier_above_top, ast_folder, AST, AST_flat, start_cyc, min_cyc, max_cyc)
    
        #gen = GenMakefile("python3", "../Tinyriscv", "tinyriscv", "clk", "rst", "tinyriscv_soc_tb.tinyriscv_soc_top_0.u_tinyriscv")
    gen.generate()


