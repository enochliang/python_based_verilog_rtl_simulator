from ast_modifier import *
from ast_schedule import AstSchedulePreprocess
from gen_wrapper import GenWrapper

from lxml import etree
import json

class GenFIWrapper(GenWrapper):
    def __init__(self,sig_dict,tb_clk,tb_rst,top_module_name,hier_above_top,ff_dir,golden_dir,obs_dir):
        GenWrapper.__init__(self,sig_dict,tb_clk,tb_rst,top_module_name,hier_above_top)

        self.NUM_STR_LEN = 4

        # Verilog Variable Declaration Name
        self.fault_free_input_tag_name = "FFI"
        self.golden_output_tag_name = "GO"

        self.FF_DIR = "ff_value/ff_value"
        self.FF_DIR = ff_dir + "/ff_value"
        self.GOLD_DIR = golden_dir + "/golden_value"
        self.OBS_DIR = obs_dir + "/result"

        self.mask_size = self.get_mask_size()


        self.INJ_ID = "inj_id"
        self.BIT_POS = "bit_pos"

        self.INPUT_FLG = "input_flag"
        self.INJ_FLG = "inj_flag"

        # File Pointer
        self.CTRL_FP = "f_control"
        self.INPUT_FP = "f_input"
        self.GOLD_FP = "f_golden"
        self.OBS_FP = "f_observe"

        # Wrapper name
        self.WRAPPER_NAME = "fi_wrapper"


    def get_mask_size(self)->int:
        max_size = 0
        for sig in self.sig_dict["ff"]:
            if self.sig_dict["ff"][sig] > max_size:
                max_size = self.sig_dict["ff"][sig]
        return max_size

    def gen_param(self):
        print("parameter CLK_HALF_PERIOD = 1;")

    def gen_task(self):
        print(f"module {self.WRAPPER_NAME};\n")
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
            string += f"    num2char(num/1{'0'*i},str[{CHAR_WIDTH*(i+1)-1}:{CHAR_WIDTH*i}]);\n"
            string += f"    num = num % 1{'0'*i};\n"

        string += f"""
    num2char(num,str[7:0]);
  end
endtask"""
        print(string)

    def gen_port_connect(self):
        print(f"\n{self.top_module_name} {self.top_module_name}(")
        print(f"  .{self.tb_clk_name}({self.tb_clk_name}),")
        for sig in self.sig_dict["input"]:
            width = self.sig_dict["input"][sig]
            print(f"  .{sig}(tb_in__{sig}),")
        for idx,sig in enumerate(self.sig_dict["output"]):
            width = self.sig_dict["output"][sig]
            if idx+1 == len(self.sig_dict["output"]):
                print(f"  .{sig}({sig})")
            else:
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
        print("\n//----------------------------------------------------------------")
        print("//  FI_Wrapper Control Signals Declaration")
        print("//----------------------------------------------------------------")
        print(f"reg {self.tb_clk_name};")
        print(f"reg [{CNT_WIDTH-1}:0] {CNT_NAME};")
        print(f"reg [{8*CNT_STR_LEN-1}:0] {CNT_NAME}_str;")
        print(f"reg [{8*CNT_STR_LEN-1}:0] {CNT_NAME}_str2;")
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
        print("\n// File IO")
        print(f"integer {CTRL_FP},{INPUT_FP},{GOLD_FP},{OBS_FP};")


    def gen_reg__in_buffer(self):
        print("\n//=====================")
        print("// input port buffers")
        print("//=====================")
        for sig in self.sig_dict["input"]:
            width = self.sig_dict["input"][sig]
            print(f"reg [{width-1}:0] tb_in__{sig};")
            print(f"reg [{width-1}:0] tb_in2__{sig};")

    def gen_reg__out_buffer(self):
        print("\n//=====================")
        print("// output port buffers")
        print("//=====================")
        for sig in self.sig_dict["output"]:
            width = self.sig_dict["output"][sig]
            print(f"reg [{width-1}:0] tb_out__{sig};")

    def gen_wire__out_port(self):
        print("\n//=====================")
        print("// output port wire")
        print("//=====================")
        for sig in self.sig_dict["output"]:
            width = self.sig_dict["output"][sig]
            print(f"wire [{width-1}:0] {sig};")

    def gen_reg__ff_reg_buffer(self):
        print("\n//=============================")
        print("// fault free register buffers")
        print("//=============================")
        for sig in self.sig_dict["ff"]:
            width = self.sig_dict["ff"][sig]
            sig_name = sig.replace("[","__").replace("]","").replace(".","__")
            print(f"reg [{width-1}:0] ff_buf__{sig_name};")

    def gen_reg__golden_reg_buffer(self):
        print("\n//=============================")
        print("// golden register buffers")
        print("//=============================")
        for sig in self.sig_dict["ff"]:
            width = self.sig_dict["ff"][sig]
            sig_name = sig.replace("[","__").replace("]","").replace(".","__")
            print(f"reg [{width-1}:0] golden_buf__{sig_name};")

    def gen_inj_flow(self):
        print('initial begin')
        print(f'  {self.tb_clk_name} = 0;')
        print(f'  { self.INJ_FLG } = 0;')
        print(f'  { self.INPUT_FLG } = 0;\n')

        print(f'  { self.CTRL_FP } = $fopen("control.txt","r");')
        print(f'  $fscanf({ self.CTRL_FP }, "%d", { self.CNT_NAME });')
        print(f'  $fscanf({ self.CTRL_FP }, "%d", { self.INJ_ID });')
        print(f'  $fscanf({ self.CTRL_FP }, "%d", { self.BIT_POS });')
        print(f'  $fclose({ self.CTRL_FP });\n')

        print(f'  num2str({ self.INJ_ID }, { self.INJ_ID }_str);')
        print(f'  num2str({ self.BIT_POS }, { self.BIT_POS }_str);')
        print(f'  cycle2num({self.CNT_NAME},{self.CNT_NAME}_str);')
        print(f'  cycle2num({self.CNT_NAME}+1,{self.CNT_NAME}_str2);')
        print(f'  setmask({ self.BIT_POS }, mask);\n')

        # load fault free input buffer
        print(f'\n  //==============================')
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
        print(f'  $fclose({self.INPUT_FP});')

        # load golden buffer
        print(f'\n  //==============================')
        print(f'  // load golden output buffer')
        print(f'  //==============================')
        print(f'  {self.GOLD_FP} = $fopen({{"{self.GOLD_DIR}_C",{self.CNT_NAME}_str2,".txt"}},"r");')
        for sig in self.sig_dict["ff"]:
            gold_buf_name = "golden_buf__"+sig.replace("[","__").replace("]","").replace(".","__")
            print(f'  $fscanf({self.GOLD_FP},"%b",{gold_buf_name});')
        print(f'  $fclose({self.GOLD_FP});')

        # timing control
        print("\n  //================")
        print("  // timing control")
        print("  //================")
        print(f"  #CLK_HALF_PERIOD {self.INPUT_FLG} = !{self.INPUT_FLG};")
        print(f"  #CLK_HALF_PERIOD {self.INJ_FLG} = !{self.INJ_FLG};")
        print(f"  #CLK_HALF_PERIOD {self.tb_clk_name} = !{self.tb_clk_name};")
        print(f"  #CLK_HALF_PERIOD {self.INPUT_FLG} = !{self.INPUT_FLG};")
        print(f"  #CLK_HALF_PERIOD {self.tb_clk_name} = !{self.tb_clk_name};")
        print(f"  #CLK_HALF_PERIOD;")

        # dump fault effect observation
        print(f'\n  //===============================')
        print(f'  // dump fault effect observation')
        print(f'  //===============================')
        print(f'  {self.OBS_FP} = $fopen({{"{self.OBS_DIR}_C", {self.CNT_NAME}_str, "_R", {self.INJ_ID}_str, "_B", {self.BIT_POS}_str , ".txt"}},"w");')
        for sig in self.sig_dict["ff"]:
            gold_buf_name = "golden_buf__"+sig.replace("[","__").replace("]","").replace(".","__")
            print(f'  $fwrite({self.OBS_FP},"%b\\n", {gold_buf_name} ^ {self.WRAPPER_NAME}.{sig});')
        print(f'  $fclose({self.OBS_FP});')
        print("end")

        print(f'\n//===============================')
        print(f'// always blocks')
        print(f'//===============================')
        print(f"// fault free pattern filling (to registers)")
        print(f"always@(posedge {self.INPUT_FLG})begin")
        for sig in self.sig_dict["ff"]:
            ff_buf_name = "ff_buf__"+sig.replace("[","__").replace("]","").replace(".","__")
            print(f'  {sig} <= {ff_buf_name};')
        print(f"end")
        print(f"\n// fault injection")
        print(f"always@(posedge {self.INJ_FLG})begin")
        print(f"  case({ self.INJ_ID })")
        for idx, sig in enumerate(self.sig_dict["ff"]):
            width = self.sig_dict["ff"][sig]
            print(f"    'd{idx}: {sig} <= {sig}^mask[{width-1}:0];")
        print(f"  endcase")
        print(f"end")
        print(f"\n// input sequence")
        print(f"always@(posedge {self.tb_clk_name} )begin")
        for sig in self.sig_dict["input"]:
            ff_buf_name = "tb_in__"+sig.replace("[","__").replace("]","").replace(".","__")
            ff_buf_name2 = "tb_in2__"+sig.replace("[","__").replace("]","").replace(".","__")
            print(f"  {ff_buf_name} <= {ff_buf_name2};")
        print(f"end")
        print(f"endmodule")


    def generate(self):
        self.gen_task()
        self.gen_param()
        self.gen_reg()
        self.gen_port_connect()
        self.gen_fptr()
        self.gen_inj_flow()

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
    parser.add_argument("--golden_value_dir", type=str, help="golden value dir")                  # Positional argument
    parser.add_argument("--result_dir", type=str, help="result dir")                  # Positional argument
    # Step 3: Parse the arguments
    args = parser.parse_args()
    tb_clk = args.tb_clk 
    tb_rst = args.tb_rst 
    top_module_name = args.top_module_name 
    hier_above_top = args.hier_above_top 
    ff_value_dir = args.ff_value_dir 
    sig_list_dir = args.sig_list_dir 
    golden_value_dir = args.golden_value_dir 
    result_dir = args.result_dir 
    
    f = open(sig_list_dir+"/fsim_sig_table.json","r")
    sig_dict = json.load(f)
    gen = GenFIWrapper(sig_dict,tb_clk,tb_rst,top_module_name,hier_above_top,ff_value_dir,golden_value_dir,result_dir)
    gen.generate()

