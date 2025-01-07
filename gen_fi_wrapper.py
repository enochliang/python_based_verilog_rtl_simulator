from ast_modifier import *
from ast_schedule import AstSchedulePreprocess
from gen_wrapper import GenWrapper

from lxml import etree
import json

class GenFIWrapper(GenWrapper):
    def __init__(self,sig_dict):
        GenWrapper.__init__(self,sig_dict)

        self.NUM_STR_LEN = 4

        # Verilog Variable Declaration Name
        self.fault_free_input_tag_name = "FFI"
        self.golden_output_tag_name = "GO"

        self.FF_DIR = "ff_value/ff_value"
        self.GOLD_DIR = "golden_value/golden_value"

        self.mask_size = self.get_mask_size()

        # File Pointer
        self.CTRL_FP = "f_control"
        self.INPUT_FP = "f_input"
        self.GOLD_FP = "f_golden"
        self.OBS_FP = "f_observe"


    def get_mask_size(self)->int:
        max_size = 0
        for sig in self.sig_dict["ff"]:
            if self.sig_dict["ff"][sig] > max_size:
                max_size = self.sig_dict["ff"][sig]
        return max_size

    def gen_task(self):
        string = """
//=============================
// Tasks
//============================="""
        print(string)
        self.gen_task__setmask()
        self.gen_task__cycle2num()
        self.gen_task__num2char()
        self.gen_task__num2str()

    def gen_task__setmask(self):
        MASK_WIDTH = self.mask_size
        # setmask() task
        string = f"""
task setmask;
  input [31:0] num;
  output [{MASK_WIDTH-1}:0] o_mask;
  begin
    o_mask = 1 << num;
  end
endtask"""
        print(string)

    def gen_task__num2str(self):
        # constants
        CHAR_WIDTH = 8
        NUM_STR_LEN = self.NUM_STR_LEN
        NUM_STR_WIDTH = CHAR_WIDTH * NUM_STR_LEN

        # generate verilog code
        string = f"""
task num2str;
  input [31:0] num;
  output [{NUM_STR_WIDTH-1}:0] str;
  begin
"""
        for i in range(NUM_STR_LEN-1,0,-1):
            string += f"    num2char(cyc/1{'0'*i},str[{CHAR_WIDTH*(i+1)-1}:{CHAR_WIDTH*i}]);\n"
            string += f"    cyc = cyc % 1{'0'*i};\n"

        string += f"""
    num2char(num,str[7:0]);
  end
endtask"""
        print(string)

    def gen_port_connect(self):
        print("(")
        for sig in self.sig_dict["input"]:
            width = self.sig_dict["input"][sig]
            print(f"  .{sig}(tb_in__{sig}),")
        for sig in self.sig_dict["output"]:
            width = self.sig_dict["output"][sig]
            print(f"  .{sig}({sig}),")
        print(");")

    def gen_reg(self):
        self.gen_reg__fi_control()
        self.gen_reg__in_buffer()
        self.gen_reg__out_buffer()
        self.gen_wire__out_port()
        self.gen_reg__ff_reg_buffer()
        self.gen_reg__golden_reg_buffer()

    def gen_reg__fi_control(self):
        MASK_WIDTH = self.mask_size
        CNT_NAME = self.CNT_NAME
        CNT_WIDTH = self.cnt_width
        CNT_STR_LEN = self.cnt_str_len

        NUM_STR_LEN = self.NUM_STR_LEN
        print("//----------------------------------------------------------------")
        print("//  FI_Wrapper Control Signals Declaration")
        print("//----------------------------------------------------------------")
        print(f"reg [{CNT_WIDTH-1}:0] {CNT_NAME}")
        print(f"reg [{8*CNT_STR_LEN-1}:0] {CNT_NAME}_str")
        print(f"reg [{8*CNT_STR_LEN-1}:0] {CNT_NAME}_str2")
        print(f"reg [31:0] inj_id;")
        print(f"reg [{8*NUM_STR_LEN-1}:0] inj_id_str;")
        print(f"reg [31:0] bit_pos;")
        print(f"reg [{8*NUM_STR_LEN-1}:0] bit_pos_str;")
        print(f"reg [{MASK_WIDTH-1}:0] mask;")
        print(f"reg inj_flag;")
        print(f"reg input_flag;")

    def gen_fptr(self):
        CTRL_FP = self.CTRL_FP
        INPUT_FP = self.INPUT_FP
        GOLD_FP = self.GOLD_FP
        OBS_FP = self.OBS_FP
        print("// File IO")
        print(f"integer {CTRL_FP},{INPUT_FP},{GOLD_FP},{OBS_FP};")


    def gen_reg__in_buffer(self):
        print("//=====================")
        print("// input port buffers")
        print("//=====================")
        for sig in self.sig_dict["input"]:
            width = self.sig_dict["input"][sig]
            print(f"reg [{width-1}:0] tb_in__{sig};")
            print(f"reg [{width-1}:0] tb_in2__{sig};")

    def gen_reg__out_buffer(self):
        print("//=====================")
        print("// output port buffers")
        print("//=====================")
        for sig in self.sig_dict["output"]:
            width = self.sig_dict["output"][sig]
            print(f"reg [{width-1}:0] tb_out__{sig};")

    def gen_wire__out_port(self):
        print("//=====================")
        print("// output port wire")
        print("//=====================")
        for sig in self.sig_dict["output"]:
            width = self.sig_dict["output"][sig]
            print(f"wire [{width-1}:0] {sig};")

    def gen_reg__ff_reg_buffer(self):
        print("//=============================")
        print("// fault free register buffers")
        print("//=============================")
        for sig in self.sig_dict["ff"]:
            width = self.sig_dict["ff"][sig]
            sig_name = sig.replace("[","__").replace("]","").replace(".","__")
            print(f"reg [{width-1}:0] ff_buf__{sig_name};")

    def gen_reg__golden_reg_buffer(self):
        print("//=============================")
        print("// golden register buffers")
        print("//=============================")
        for sig in self.sig_dict["ff"]:
            width = self.sig_dict["ff"][sig]
            sig_name = sig.replace("[","__").replace("]","").replace(".","__")
            print(f"reg [{width-1}:0] golden_buf__{sig_name};")

    def gen_inj_flow(self):
        print('initial begin')
        print('  tb_clk = 0;')
        print('  tb_reset_n = 1;')
        print('  inj_flag = 0;')
        print('  input_flag = 0;\n')

        print(f'  f_control = $fopen("control.txt","r");')
        print(f'  $fscanf({self.CTRL_FP},"%d",cycle);')
        print(f'  $fscanf({self.CTRL_FP},"%d",inj_id);')
        print(f'  num2str(inj_id,inj_id_str);')
        print(f'  $fscanf({self.CTRL_FP},"%d",bit_pos);')
        print(f'  num2str(,bit_pos_str);')
        print(f'  $fclose({self.CTRL_FP});')

        print(f'  cycle2num({self.CNT_NAME},{self.CNT_NAME}_str);')
        print(f'  cycle2num({self.CNT_NAME}+1,{self.CNT_NAME}_str2);')

        print(f'  setmask(bit_pos,mask);')

        # load fault free input buffer
        print(f'  //==============================')
        print(f'  // load fault free input buffer')
        print(f'  //==============================')
        print(f'  {self.INPUT_FP} = $fopen({{"{self.FF_DIR}_C",{self.CNT_NAME}_str,".txt"}},"r");')
        for sig in self.sig_dict["ff"]:
            ff_buf_name = "ff_buf__"+sig.replace("[","__").replace("]","").replace(".","__")
            print(f'  $fscanf({self.INPUT_FP},"%b",{ff_buf_name});')
        for sig in self.sig_dict["input"]:
            ff_buf_name = "tb_in__"+sig.replace("[","__").replace("]","").replace(".","__")
            print(f'  $fscanf({self.INPUT_FP},"%b",{ff_buf_name});')
        for sig in self.sig_dict["input"]:
            ff_buf_name = "tb_in2__"+sig.replace("[","__").replace("]","").replace(".","__")
            print(f'  $fscanf({self.INPUT_FP},"%b",{ff_buf_name});')

        # load golden buffer
        print(f'  //==============================')
        print(f'  // load golden output buffer')
        print(f'  //==============================')
        print(f'  {self.GOLD_FP} = $fopen({{"{self.GOLD_DIR}_C",{self.CNT_NAME}_str2,".txt"}},"r");')
        for sig in self.sig_dict["ff"]:
            gold_buf_name = "ff_buf__"+sig.replace("[","__").replace("]","").replace(".","__")
            print(f'  $fscanf({self.GOLD_FP},"%b",{gold_buf_name});')

        # load

        print("end")

    def generate(self):
        self.gen_task()
        self.gen_reg()
        self.gen_port_connect()
        self.gen_fptr()
        self.gen_inj_flow()

if __name__ == "__main__":
    
    f = open("sig_list/fsim_sig_table.json","r")
    sig_dict = json.load(f)
    gen = GenFIWrapper(sig_dict)
    gen.generate()

