from ast_modifier import *
from ast_schedule import AstSchedulePreprocess
from gen_wrapper import GenWrapper

from lxml import etree
import json

class GenPySimFFWrapper(GenWrapper):
    def __init__(self,sig_dict,tb_clk,tb_rst,top_module_name,hier_above_top,ff_value_dir):
        GenWrapper.__init__(self,sig_dict,tb_clk,tb_rst,top_module_name,hier_above_top)

        self.ff_value_dir = ff_value_dir
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
        FFI_DIR = self.ff_value_dir + "/ff_value"
        CNT_NAME = self.CNT_NAME
        CNT_STR = self.CNT_NAME + "_str"
        CNT_STR_LEN = self.cnt_str_len

        sig_list = self.sig_list

        string = f"""
//============================
// Dump Logic Value for Pysim
//============================
integer {FFI};
always@(posedge {CLK}) begin
  if({RST}) begin
    if(1) begin
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
    # Step 1: Create the parser
    parser = argparse.ArgumentParser(description="A simple example of argparse usage.")

    # Step 2: Define arguments
    parser.add_argument("--tb_clk", type=str, help="tb clk name")                  # Positional argument
    parser.add_argument("--tb_rst", type=str, help="tb rst name")                  # Positional argument
    parser.add_argument("--top_module_name", type=str, help="top module name")                  # Positional argument
    parser.add_argument("--hier_above_top", type=str, help="hier above top")                  # Positional argument
    parser.add_argument("--ff_value_dir", type=str, help="ff value dir")                  # Positional argument
    parser.add_argument("--sig_list_dir", type=str, help="sig list dir")                  # Positional argument
    # Step 3: Parse the arguments
    args = parser.parse_args()
    tb_clk = args.tb_clk 
    tb_rst = args.tb_rst 
    top_module_name = args.top_module_name 
    hier_above_top = args.hier_above_top 
    ff_value_dir = args.ff_value_dir 
    sig_list_dir = args.sig_list_dir 
    
    f = open(sig_list_dir+"/pysim_sig_table.json","r")
    sig_dict = json.load(f)
    gen = GenPySimFFWrapper(sig_dict,tb_clk,tb_rst,top_module_name,hier_above_top,ff_value_dir)
    gen.generate()

