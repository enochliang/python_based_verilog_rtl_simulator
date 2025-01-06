from ast_modifier import *
from ast_schedule import AstSchedulePreprocess

from lxml import etree
import json

class GenPySimFFWrapper:
    def __init__(self,sig_dict):
        self.sig_dict = sig_dict
        self.tb_clk_name = "clk"
        self.tb_rst_name = "resetn"

        # Verilog Variable Declaration Name
        self.cycle_cnt = ("cycle",32)

        self.cnt_name = "cycle"
        self.cnt_width = 32
        self.cnt_str_len = 7

        self.ff_value_dir = "pysim_ff_value/ff_value"
        self.ff_file_ptr = "ffi_f"

    def print_strs(self,l:list):
        for s in l:
            print(s)

    def gen_cnt(self)->list:
        CLK = self.tb_clk_name
        RST = self.tb_rst_name
        CNT_NAME = self.cnt_name
        CNT_WIDTH = self.cnt_width

        string = f"""
//=============================
// Generate Counter
//=============================
reg [{CNT_WIDTH-1}:0] {CNT_NAME};
always@(posedge {CLK}) begin
  if(!{RST}) {CNT_NAME} <= 0;
  else            {CNT_NAME} <= {CNT_NAME} + 1;
end"""
        print(string)

    def gen_task(self)->list:
        CHAR_WIDTH = 8
        CNT_STR_LEN = self.cnt_str_len
        CNT_STR_WIDTH = CHAR_WIDTH * CNT_STR_LEN
        CNT_WIDTH = self.cnt_width
        string = f"""
//=============================
// Tasks
//=============================
task cycle2num;
  input [{CNT_WIDTH-1}:0] cyc;
  output [{CNT_STR_WIDTH-1}:0] num;
  begin"""
        for i in range(CNT_STR_LEN-1,0,-1):
            string = string + f"    num2char(cyc/1{'0'*i},num[{CHAR_WIDTH*(i+1)-1}:{CHAR_WIDTH*i}]);\n"
            string = string + f"    cyc = cyc % 1{'0'*i};\n"

        string = string + """
    num2char(cyc,num[7:0]);",
  end
endtask

task num2char;
  input [31:0] num;
  output [7:0] ch;
  begin
    case(num)
      'd0:ch=8'd48;
      'd1:ch=8'd49;
      'd2:ch=8'd50;
      'd3:ch=8'd51;
      'd4:ch=8'd52;
      'd5:ch=8'd53;
      'd6:ch=8'd54;
      'd7:ch=8'd55;
      'd8:ch=8'd56;
      'd9:ch=8'd57;
    endcase
  end
endtask"""
        print(string)


    def gen_ff_input_dump_code(self)->str:
        CLK = self.tb_clk_name
        RST = self.tb_rst_name
        FFI = self.ff_file_ptr
        FFI_DIR = self.ff_value_dir
        CNT_NAME = self.cnt_name
        CNT_STR = self.cnt_name + "_str"
        CNT_STR_LEN = self.cnt_str_len
        sig_list = list(self.sig_dict.keys())
        for i,var in enumerate(sig_list):
            if "picorv32_axi." in var:
                sig_list[i] = var.replace("picorv32_axi.","top.uut.")
            else:
                sig_list[i] = "top.uut."+var

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
        #string = string + self.gen_tb_head()
        self.gen_cnt()
        self.gen_ff_input_dump_code()
        #string = string + self.gen_tb_tail()

if __name__ == "__main__":
    
    f = open("sig_list/pysim_sig_table.json","r")
    sig_dict = json.load(f)
    gen = GenPySimFFWrapper(sig_dict)
    gen.generate()

