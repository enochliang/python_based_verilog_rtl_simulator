from ast_modifier import *
from ast_schedule import AstSchedulePreprocess

from lxml import etree
import json

class GenWrapper:
    def __init__(self,sig_dict,tb_clk,tb_rst,top_module_name,hier_above_top):
        self.sig_dict = sig_dict
        self.tb_clk_name = tb_clk
        self.tb_rst_name = tb_rst

        # Verilog Variable Declaration Name
        self.CNT_NAME = "cycle"
        self.cnt_width = 32
        self.cnt_str_len = 7

        # design module info
        self.top_module_name = top_module_name
        self.hier_above_top = hier_above_top

    def gen_cnt(self)->list:
        CLK = self.tb_clk_name
        RST = self.tb_rst_name
        CNT_NAME = self.CNT_NAME
        CNT_WIDTH = self.cnt_width
        CNT_STR = self.CNT_NAME + "_str"
        CNT_STR_LEN = self.cnt_str_len

        string = f"""
//=============================
// Generate Counter
//=============================
reg [{CNT_WIDTH-1}:0] {CNT_NAME};
reg [{CNT_STR_LEN*8-1}:0] {CNT_STR};

always@(posedge {CLK}) begin
  if(!{RST}) {CNT_NAME} <= 0;
  else       {CNT_NAME} <= {CNT_NAME} + 1;
  cycle2num({CNT_NAME}, {CNT_STR});
end"""
        print(string)


    def gen_task__cycle2num(self):
        # constants
        CHAR_WIDTH = 8
        CNT_STR_LEN = self.cnt_str_len
        CNT_STR_WIDTH = CHAR_WIDTH * CNT_STR_LEN
        CNT_WIDTH = self.cnt_width

        # generate verilog code
        string = f"""
task cycle2num;
  input [{CNT_WIDTH-1}:0] cyc;
  output [{CNT_STR_WIDTH-1}:0] num;
  begin
"""
        for i in range(CNT_STR_LEN-1,0,-1):
            string += f"    num2char(cyc/1{'0'*i},num[{CHAR_WIDTH*(i+1)-1}:{CHAR_WIDTH*i}]);\n"
            string += f"    cyc = cyc % 1{'0'*i};\n"

        string += f"""
    num2char(cyc,num[7:0]);
  end
endtask"""
        print(string)

    def gen_task__num2char(self):
        string = """
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





if __name__ == "__main__":
    
    f = open("sig_list/fsim_sig_table.json","r")
    sig_dict = json.load(f)
    #f.close()
    #fl = GenFaultList(1037,sig_dict)
    #fl.get_fault_list()
    gen = GenFFWrapper(sig_dict)
    gen.generate()

