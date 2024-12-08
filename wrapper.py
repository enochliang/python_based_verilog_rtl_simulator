from lxml import etree
import json

class GenSimFFWrapper:
    def __init__(self,sig_dict):
        self.sig_dict = sig_dict
        self.tb_clk_name = "clk"
        self.tb_rst_name = "resetn"

        # Verilog Variable Declaration Name
        self.fault_free_input_tag_name = "FFI"
        self.golden_output_tag_name = "GO"
        self.cycle_cnt = ("cycle",32)

        
        self.cnt_name = "cycle"
        self.cnt_width = 32
        self.cnt_num_digit = 7

    def print_strs(self,l:list):
        for s in l:
            print(s)

    def gen_cnt(self)->list:
        CLK = self.tb_clk_name
        RST = self.tb_rst_name
        CNT_NAME = self.cnt_name
        CNT_WIDTH = self.cnt_width

        string = [f'reg [{CNT_WIDTH-1}:0] {CNT_NAME};',
                  f'always@(posedge {CLK}) begin',
                  f'  if(!{RST}) {CNT_NAME} <= 0;',
                  f'  else            {CNT_NAME} <= {CNT_NAME} + 1;',
                  f'end']
        return string

    def gen_task(self)->list:
        CHAR_WIDTH = 8
        CNT_NUM_DIGIT = self.cnt_num_digit
        CNT_STR_WIDTH = CHAR_WIDTH * CNT_NUM_DIGIT
        CNT_WIDTH = self.cnt_width
        string = ["task cycle2num;",
                  f"  input [{CNT_WIDTH-1}:0] cyc;",
                  f"  output [{CNT_STR_WIDTH-1}:0] num;",
                  "  begin"]
        for i in range(CNT_NUM_DIGIT-1,0,-1):
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
        CNT_NAME = self.cnt_name
        CNT_NUM_DIGIT = self.cnt_num_digit
        sig_list = list(self.sig_dict.keys())
        for i,var in enumerate(sig_list):
            if "picorv32_axi." in var:
                sig_list[i] = var.replace("picorv32_axi.","top.uut.")
            else:
                sig_list[i] = "top.uut."+var
                

        string =          [f'  reg [{CNT_NUM_DIGIT*8-1}:0] {CNT_NAME}_num;',
                           f'  integer ffi_f;',
                           f'  always@(posedge {CLK}) begin',
                           f'    if({RST} && {CNT_NAME}>=0)begin',
                           f'      if({CNT_NAME}<1037)begin',
                           f'        cycle2num({CNT_NAME},{CNT_NAME}_num);']
        string = string + [f'        ffi_f = $fopen('+'{'+f'"pattern/FaultFree_Signal_Value_C",{CNT_NAME}_num,".txt"'+'},"w");']
        string = string + [f'        $fwrite(ffi_f,"%b\\n",{varname});' for varname in sig_list]
        string = string + [f'        $fclose(ffi_f);',
                           f'      end',
                           f'    end',
                           f'  end',
                           ""]

        return string
    

    def generate(self):
        print("====================================")
        print("Start Generating Fault Free Wrapper:")
        print("====================================")
        string = self.gen_task()
        string = string + self.gen_tb_head()
        string = string + self.gen_cnt()
        string = string + self.gen_ff_input_dump_code()
        string = string + self.gen_tb_tail()

        for s in string:
            print(s)



class DumpSigList:
    def __init__(self,ast):
        self.ast = ast

    def dump_sig_list(self):
        parser = AST_Parser(self.ast)
        sig_dict = parser.get_signal_dicts()
        f = open("sig_dict.json","w")
        f.write(json.dumps(sig_dict, sort_keys=True, indent=4))
        f.close()



class GenFaultList:
    def __init__(self,cycle:int,_sig_dict:dict):
        self.total_cyc = cycle
        self.sig_dict = _sig_dict
        
    def get_fault_list(self):
        self.all_fault_list = []
        for cyc in range(self.total_cyc):
            for idx,sig_name in enumerate(self.sig_dict["ff"]):
                width = self.sig_dict["ff"][sig_name]
                for bit in range(width):
                    self.all_fault_list.append((cyc,idx,bit))

        #pprint.pp(self.all_fault_list)

if __name__ == "__main__":
    #ast_file = "./ast/Vsha1.xml"
    #ast = Verilator_AST_Tree(ast_file)
    #parser = AST_Parser(ast)
    
    #dumper = DumpSigList(ast)
    #dumper.dump_sig_list()
    
    f = open("graph_sig_dict.json","r")
    sig_dict = json.load(f)
    #f.close()
    #fl = GenFaultList(1037,sig_dict)
    #fl.get_fault_list()
    gen = GenSimFFWrapper(sig_dict)
    l = gen.gen_cnt()
    gen.print_strs(l)
    l = gen.gen_task()
    gen.print_strs(l)
    l= gen.gen_ff_input_dump_code()
    gen.print_strs(l)
    #gen.generate()
    #gen = Gen_FI_Wrapper(sig_dict)
    #gen.generate()

