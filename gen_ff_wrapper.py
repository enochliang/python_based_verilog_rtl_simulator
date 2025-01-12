from ast_modifier import *
from ast_schedule import AstSchedulePreprocess
from gen_wrapper import GenWrapper

from lxml import etree
import json

class GenFFWrapper(GenWrapper):
    def __init__(self,sig_dict):
        GenWrapper.__init__(self,sig_dict)

        self.ff_value_dir = "ff_value/ff_value"
        self.ff_file_ptr = "ffi_f"
        self.golden_value_dir = "golden_value/golden_value"
        self.golden_file_ptr = "go_f"

        self.get_ff_sig_list()

    def get_ff_sig_list(self):
        TOP_MODULE = self.top_module_name
        HIER_ABOVE = self.hier_above_top
        self.sig_list = {"input":[],"ff":[],"output":[]}
        for cls in self.sig_dict:
            for var in self.sig_dict[cls].keys():
                if TOP_MODULE+"." in var:
                    self.sig_list[cls].append(var.replace(TOP_MODULE+".",HIER_ABOVE+"."))
                else:
                    self.sig_list[cls].append(HIER_ABOVE+"."+var)

    def gen_task(self):
        string = """
//=============================
// Tasks
//============================="""
        print(string)
        self.gen_task__cycle2num()
        self.gen_task__num2char()

    def gen_code__dump_ff_value(self):
        # constant
        CLK = self.tb_clk_name
        RST = self.tb_rst_name
        FFI = self.ff_file_ptr
        FFI_DIR = self.ff_value_dir
        GO = self.golden_file_ptr
        GO_DIR = self.golden_value_dir
        CNT_NAME = self.CNT_NAME
        CNT_STR = self.CNT_NAME + "_str"
        CNT_STR_LEN = self.cnt_str_len

        sig_list = self.sig_list
                
        # generate verilog code
        string = f'''
//=============================
// Dump Fault Free Value
//=============================
integer {FFI};
always@(posedge {CLK}) begin
  if({RST} && {CNT_NAME}>=0)begin
    if({CNT_NAME}>0)begin
'''
        for varname in sig_list["input"]:
            string += f'      $fwrite({FFI},"%b\\n",{varname});\n'
        string += f'''
      $fclose({FFI});
    end
    if({CNT_NAME}>=0)begin
      {FFI} = $fopen({{"{FFI_DIR}_C",{CNT_STR},".txt"}},"w");
'''
        for varname in sig_list["ff"]:
            string += f'      $fwrite(ffi_f,"%b\\n",{varname});\n'
        for varname in sig_list["input"]:
            string += f'      $fwrite(ffi_f,"%b\\n",{varname});\n'
        string += f'''
    end
  end
end
'''
        print( string)

    def gen_code__dump_golden_value(self):
        # constant
        CLK = self.tb_clk_name
        RST = self.tb_rst_name
        FFI = self.ff_file_ptr
        FFI_DIR = self.ff_value_dir
        GO = self.golden_file_ptr
        GO_DIR = self.golden_value_dir
        CNT_NAME = self.CNT_NAME
        CNT_STR = self.CNT_NAME + "_str"
        CNT_STR_LEN = self.cnt_str_len

        sig_list = self.sig_list
                
        # generate verilog code
        string = f'''
//=============================
// Dump Golden Value
//=============================
integer {GO};
always@(posedge {CLK}) begin
  if({RST})begin
    if({CNT_NAME}>0)begin
      {GO} = $fopen({{"{GO_DIR}_C",{CNT_STR},".txt"}},"w");
'''
        for varname in sig_list["ff"]:
            string += f'      $fwrite({GO},"%b\\n",{varname});\n'
        string += f'''
      $fclose({GO});
    end
  end
end
'''
        print( string)

    def generate(self):
        self.gen_task()
        self.gen_cnt()
        self.gen_code__dump_ff_value()
        self.gen_code__dump_golden_value()



if __name__ == "__main__":
    
    f = open("sig_list/fsim_sig_table.json","r")
    sig_dict = json.load(f)
    gen = GenFFWrapper(sig_dict)
    gen.generate()

