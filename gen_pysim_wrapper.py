from ast_modifier import *
from ast_schedule import AstSchedulePreprocess
from gen_wrapper import GenWrapper

from lxml import etree
import json

class GenPySimFFWrapper(GenWrapper):
    def __init__(self,sig_dict):
        GenWrapper.__init__(self,sig_dict)

        self.ff_value_dir = "pysim_ff_value/ff_value"
        self.ff_file_ptr = "ffi_f"

        self.get_pysim_sig_list()

    def get_pysim_sig_list(self):
        TOP_MODULE = self.top_module_name
        HIER_ABOVE = self.hier_above_top
        self.sig_list = list(self.sig_dict.keys())
        for i,var in enumerate(self.sig_list):
            if TOP_MODULE+"." in var:
                self.sig_list[i] = var.replace(TOP_MODULE+".",HIER_ABOVE+".")
            else:
                self.sig_list[i] = HIER_ABOVE+"."+var

    def gen_task(self):
        string = """
//=============================
// Tasks
//============================="""
        print(string)
        self.gen_task__cycle2num()
        self.gen_task__num2char()

    def gen_code__dump_ff_value(self)->str:
        CLK = self.tb_clk_name
        RST = self.tb_rst_name
        FFI = self.ff_file_ptr
        FFI_DIR = self.ff_value_dir
        CNT_NAME = self.CNT_NAME
        CNT_STR = self.CNT_NAME + "_str"
        CNT_STR_LEN = self.cnt_str_len

        sig_list = self.sig_list

        string = f"""
//============================
// Generate Counter String
//============================
reg [{CNT_STR_LEN*8-1}:0] {CNT_STR};

//============================
// Dump Logic Value for Pysim
//============================
integer {FFI};
always@(posedge {CLK}) begin
  if({RST}) begin
    if(1) begin
      cycle2num({CNT_NAME},{CNT_STR});
      {FFI} = $fopen({{"{FFI_DIR}_C", {CNT_STR}, ".txt"}}, "w");
"""
        for varname in sig_list:
            string = string + f'      $fwrite({FFI},"%b\\n",{varname});\n'

        string = string + f"""
      $fclose({FFI});
    end
  end
end
"""
        print(string)
    

    def generate(self):
        self.gen_task()
        self.gen_cnt()
        self.gen_code__dump_ff_value()

if __name__ == "__main__":
    
    f = open("sig_list/pysim_sig_table.json","r")
    sig_dict = json.load(f)
    gen = GenPySimFFWrapper(sig_dict)
    gen.generate()

