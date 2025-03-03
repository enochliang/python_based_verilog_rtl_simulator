import os
import pandas as pd
import json
import ast
from tqdm import tqdm

class RTLFSimulationError(Exception):
    def __init__(self, message, error_code):
        super().__init__(message)
        self.error_code = error_code

    def __str__(self):
        return f"{self.args[0]} (Error Code: {self.error_code})"

class GenFaultList:
    def __init__(self,sigtable_dir:str, ace_dir:str):

        f = open(sigtable_dir,"r")
        self.sig_dict = json.load(f)
        f.close()

        self.idx_2_sig_name_map = {}
        self.sig_name_2_idx_map = {}
        for idx,sig_name in enumerate(self.sig_dict["ff"]):
            self.idx_2_sig_name_map[str(idx)] = sig_name
            self.sig_name_2_idx_map[sig_name] = idx

        self.rw_table_file = ace_dir
        
        self.load_rw_table()

    def load_rw_table(self):
        self.rw_table = pd.read_csv(self.rw_table_file)
        self.rw_table_list = list()
        self.total_cyc = len(self.rw_table)
        for idx , row in self.rw_table.iterrows():
            cyc = row["cycle"]
            if idx == 0:
                self.start_cyc = cyc
            rw_events = row["rw_event"]
            rw_events = ast.literal_eval(rw_events)
            rw_row = {}
            for rw_event in rw_events:
                rw_row[rw_event["r"]] = {"w":set([w_event for w_event in rw_event["w"]]), "stay":set([w_event for w_event in rw_event["stay"]]), "ctrl":set([w_event for w_event in rw_event["ctrl"]])}
            self.rw_table_list.append(rw_row)
        print("rw table loaded")
    

    def _get_all_fault_list(self):
        self.all_fault_list = []
        for cyc in range(self.start_cyc, self.start_cyc+self.total_cyc ):
            for idx,sig_name in enumerate(self.sig_dict["ff"]):
                width = self.sig_dict["ff"][sig_name]
                for bit in range(width):
                    self.all_fault_list.append( (cyc, idx, bit) )

    def _get_ace_fault_list(self):
        self.data_fault_list = []
        self.ctrl_fault_list = []
        for cyc, rw_row in enumerate(self.rw_table_list):
            for r_event in rw_row:
                if len(rw_row[r_event]["ctrl"]) > 0:
                    width = self.sig_dict["ff"][r_event]
                    idx = self.sig_name_2_idx_map[r_event]
                    for bit in range(width):
                        self.ctrl_fault_list.append( (cyc+self.start_cyc, idx, bit) )
                    continue

                if len(rw_row[r_event]["w"]) == 0:
                    continue
                width = self.sig_dict["ff"][r_event]
                idx = self.sig_name_2_idx_map[r_event]
                for bit in range(width):
                    self.data_fault_list.append( (cyc+self.start_cyc, idx, bit) )
        print(f"ace fault list obtained")
        print(f"total data fault injection = {len(self.data_fault_list)}")
        print(f"total ctrl fault injection = {len(self.ctrl_fault_list)}")

    def setup(self):
        #self._get_all_fault_list()
        self._get_ace_fault_list()


class FaultInjection(GenFaultList):
    def __init__(self,sigtable_dir:str,ace_dir:str,fi_dir:str="./fi_sim_veri"):
        GenFaultList.__init__(self,sigtable_dir,ace_dir)
        self.fi_dir = fi_dir
        self.fsim_exe_file = f"{self.fi_dir} > fsim.log &"

    def run_all_fault_sim(self):

        self._get_all_fault_list()

        for fi_case in self.all_fault_list:
            f = open("control.txt","w")
            f.write(f"{fi_case[0]}\n{fi_case[1]}\n{fi_case[2]}")
            f.close()
            os.system(self.fsim_exe_file)
        
        self.result_stat()

    def run_data_fault_sim(self):

        self._get_ace_fault_list()

        tot = len(self.data_fault_list)
        cnt = 0
        
        print("[Progress] running fault injection...")
        with tqdm(total=tot) as pbar:
            for fi_case in self.data_fault_list:
                f = open("control.txt","w")
                f.write(f"{fi_case[0]}\n{fi_case[1]}\n{fi_case[2]}")
                f.close()
                os.system(self.fsim_exe_file)
                cnt += 1
                if cnt % 100 == 0:
                    pbar.update(100)
        print("fault injection done.")

        self.result_data_stat()

    def result_data_stat(self):
        clock_cyc_col = []
        src_bit_col = []
        dst_bit_col = []
        faulty_effect_class_col = []
        
        print("[Progress] observing fault injection result...")
        tot = len(self.data_fault_list)
        cnt = 0
        with tqdm(total=tot) as pbar:
            for fi_case in self.data_fault_list:
                # Read faulty bit
                f = open(f"result/result_C{fi_case[0]:07}_R{fi_case[1]:04}_B{fi_case[2]:04}.txt","r")
                faulty_values = f.read().split("\n")
                f.close()
                # Read golden value for unknown elimination
                f = open(f"golden_value/golden_value_C{fi_case[0]+1:07}.txt")
                golden_values = f.read().split("\n")
                f.close()

                src_reg_name = self.idx_2_sig_name_map[str(fi_case[1])]
                dst_reg_list = []
                for idx,sig_name in enumerate(self.sig_dict["ff"]):
                    width = len(faulty_values[idx])
                    if len(faulty_values[idx]) != int(self.sig_dict["ff"][sig_name]):
                        raise RTLFSimulationError("Error: Width Not Match.",1)
                    else:
                        for c_idx in range(width):
                            if golden_values[idx][width-1-c_idx] == "x":
                                continue
                            if faulty_values[idx][width-1-c_idx] == "1":
                                dst_reg_list.append(f"{sig_name}[{c_idx}]")
                clock_cyc_col.append(fi_case[0])
                src_bit_col.append(f"{src_reg_name}[{fi_case[2]}]")
                dst_bit_col.append(dst_reg_list)
                if dst_reg_list == []:
                    faulty_effect_class_col.append("masked")
                elif len(dst_reg_list) == 1:
                    faulty_effect_class_col.append("single")
                else:
                    faulty_effect_class_col.append("multiple")

                cnt += 1
                if cnt % 100 == 0:
                    pbar.update(100)


        df = pd.DataFrame({"cycle":clock_cyc_col,"src_bit":src_bit_col,"dst_bit":dst_bit_col,"fault_effect":faulty_effect_class_col})
        df.to_csv(f"fault_sim_result(data).csv")

    def result_stat(self,mode:str):
        clock_cyc_col = []
        src_bit_col = []
        dst_bit_col = []
        faulty_effect_class_col = []
        
        for fi_case in self.all_fault_list:
            f = open(f"result/result_C{fi_case[0]:07}_R{fi_case[1]:04}_B{fi_case[2]:04}.txt","r")
            faulty_values = f.read().split("\n")
            f.close()
            src_reg_name = self.idx_2_sig_name_map[str(fi_case[1])]
            dst_reg_list = []
            for idx,sig_name in enumerate(self.sig_dict["ff"]):
                if len(faulty_values[idx]) != int(self.sig_dict["ff"][sig_name]):
                    raise RTLFSimulationError("Error: Width Not Match.",1)
                else:
                    for c_idx in range(len(faulty_values[idx])):
                        if faulty_values[idx][len(faulty_values[idx])-1-c_idx] == "1":
                            dst_reg_list.append(f"{sig_name}[{c_idx}]")
            clock_cyc_col.append(fi_case[0])
            src_bit_col.append(f"{src_reg_name}[{fi_case[2]}]")
            dst_bit_col.append(dst_reg_list)
            if dst_reg_list == []:
                faulty_effect_class_col.append("masked")
            elif len(dst_reg_list) == 1:
                faulty_effect_class_col.append("single")
            else:
                faulty_effect_class_col.append("multiple")

        df = pd.DataFrame({"cycle":clock_cyc_col,"src_bit":src_bit_col,"dst_bit":dst_bit_col,"fault_effect":faulty_effect_class_col})
        df.to_csv(f"fault_sim_result({mode}).csv")

                            

if __name__ == "__main__":
    # Step 1: Create the parser
    parser = argparse.ArgumentParser(description="A simple example of argparse usage.")

    # Step 2: Define arguments
    parser.add_argument("-t",'--rwtable_dir', type=str, help="RW-table directory")
    parser.add_argument("-f", "--fsim_dir", type=str, help="fault simulator directory")                  # Positional argument
    parser.add_argument("-s", "--sigtable_dir", type=str, help="signal table directory")

    # Step 3: Parse the arguments
    args = parser.parse_args()

    if args.rwtable_dir:
        rwtable_dir = args.rwtable_dir
    else:
        rwtable_dir = None

    if args.fsim_dir:
        fsim_dir = args.fsim_dir
    else:
        fsim_dir = None

    if args.sigtable_dir:
        sigtable_dir = args.sigtable_dir
    else:
        sigtable_dir = "fsim_sig_table.json"


    inj = FaultInjection(sigtable_dir = sigtable_dir, ace_dir = rwtable_dir, fi_dir = fsim_dir)
    inj.run_data_fault_sim()

    #gen = GenFaultList(sig_dict)
    #gen.setup()
