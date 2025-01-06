from ast_modifier import *
from ast_schedule import AstSchedulePreprocess

from lxml import etree
import json

class GenFFWrapper:
    def __init__(self,sig_dict):
        self.sig_dict = sig_dict
        self.tb_clk_name = "clk"
        self.tb_rst_name = "resetn"

        # Verilog Variable Declaration Name
        self.cnt_name = "cycle"
        self.cnt_width = 32
        self.cnt_str_len = 7

        self.ff_value_dir = "ff_value/ff_value"
        self.ff_file_ptr = "ffi_f"

    def print_strs(self,l:list):
        for s in l:
            print(s)

    def gen_cnt(self)->list:
        CLK = self.tb_clk_name
        RST = self.tb_rst_name
        CNT_NAME = self.cnt_name
        CNT_WIDTH = self.cnt_width

        string = ['//=============================',
                  '// Generate Counter',
                  '//=============================']
        string = string + [f'reg [{CNT_WIDTH-1}:0] {CNT_NAME};',
                           f'always@(posedge {CLK}) begin',
                           f'  if(!{RST}) {CNT_NAME} <= 0;',
                           f'  else       {CNT_NAME} <= {CNT_NAME} + 1;',
                           f'end']
        return string

    def gen_task(self)->list:
        CHAR_WIDTH = 8
        CNT_STR_LEN = self.cnt_str_len
        CNT_STR_WIDTH = CHAR_WIDTH * CNT_STR_LEN
        CNT_WIDTH = self.cnt_width

        string = ['//=============================',
                  '// Tasks',
                  '//=============================']
        string = ["task cycle2num;",
                  f"  input [{CNT_WIDTH-1}:0] cyc;",
                  f"  output [{CNT_STR_WIDTH-1}:0] num;",
                  "  begin"]
        for i in range(CNT_STR_LEN-1,0,-1):
            string = string + [f"    num2char(cyc/1{'0'*i},num[{CHAR_WIDTH*(i+1)-1}:{CHAR_WIDTH*i}]);",
                               f"    cyc = cyc % 1{'0'*i};"]

        string = string + ["    num2char(cyc,num[7:0]);",
                  "  end",
                  "endtask",
                  "",
                  "task num2char;",
                  "  input [31:0] num;",
                  "  output [7:0] ch;",
                  "  begin",
                  "    case(num)",
                  "      'd0:ch=8'd48;",
                  "      'd1:ch=8'd49;",
                  "      'd2:ch=8'd50;",
                  "      'd3:ch=8'd51;",
                  "      'd4:ch=8'd52;",
                  "      'd5:ch=8'd53;",
                  "      'd6:ch=8'd54;",
                  "      'd7:ch=8'd55;",
                  "      'd8:ch=8'd56;",
                  "      'd9:ch=8'd57;",
                  "    endcase",
                  "  end",
                  "endtask"]
        return string


    def gen_ff_input_dump_code(self)->str:
        CLK = self.tb_clk_name
        RST = self.tb_rst_name
        FFI = self.fault_free_input_tag_name
        FFI_DIR = self.ff_value_dir
        CNT_NAME = self.cnt_name
        CNT_STR = self.cnt_name + "_str"
        CNT_STR_LEN = self.cnt_str_len
        sig_list = {"input":[],"ff":[],"output":[]}
        for cls in sig_dict:
            for var in sig_dict[cls].keys():
                if "picorv32_axi." in var:
                    sig_list[cls].append(var.replace("picorv32_axi.","top.uut."))
                else:
                    sig_list[cls].append("top.uut."+var)
                

        string =          [f'  reg [{CNT_STR_LEN*8-1}:0] {CNT_STR};',
                           f'  integer {FFI};',
                           f'  always@(posedge {CLK}) begin',
                           f'    if({RST} && {CNT_NAME}>=0)begin',
                           f'      if({CNT_NAME}>0)begin']
        string = string + [f'        $fwrite({FFI},"%b\\n",{varname});' for varname in sig_list["input"]]
        string = string + [f'        $fclose({FFI});',
                           f'      end',
                           f'      if({CNT_NAME}>=0)begin',
                           f'        cycle2num({CNT_NAME},{CNT_STR});']
        string = string + [f'        {FFI} = $fopen('+'{'+f'"{FFI_DIR}_C",{CNT_STR},".txt"'+'},"w");']
        string = string + [f'        $fwrite(ffi_f,"%b\\n",{varname});' for varname in sig_list["ff"]]
        string = string + [f'        $fwrite(ffi_f,"%b\\n",{varname});' for varname in sig_list["input"]]
        string = string + [f'      end',
                           f'    end',
                           f'  end',
                           ""]

        string = string + [f'  integer go_f;',
                           f'  always@(posedge {CLK}) begin',
                           f'    if({RST})begin',
                           f'      if({CNT_NAME}>0)begin',
                           f'        cycle2num({CNT_NAME},{CNT_NAME}_num);']
        string = string + [f'        go_f = $fopen('+'{'+f'"golden_value/Golden_Signal_Value_C",{CNT_NAME}_num,".txt"'+'},"w");']
        string = string + [f'        $fwrite(go_f,"%b\\n",{varname});' for varname in sig_list["ff"]]
        string = string + [f'        $fclose(ffi_f);']
        string = string + [f'      end',
                           f'    end',
                           f'  end',
                           ""]

        return string

    def generate(self):
        print("====================================")
        print("Start Generating Fault Free Wrapper:")
        print("====================================")
        string = self.gen_task()
        #string = string + self.gen_tb_head()
        string = string + self.gen_cnt()
        string = string + self.gen_ff_input_dump_code()
        #string = string + self.gen_tb_tail()

        for s in string:
            print(s)



if __name__ == "__main__":
    
    f = open("sig_list/fsim_sig_table.json","r")
    sig_dict = json.load(f)
    #f.close()
    #fl = GenFaultList(1037,sig_dict)
    #fl.get_fault_list()
    gen = GenFFWrapper(sig_dict)
    gen.generate()

