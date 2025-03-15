import os
import pandas as pd
import json
import ast
from tqdm import tqdm
import argparse
import pprint

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

        self.sigid_2_signame = {}
        self.signame_2_sigid = {}
        self.total_cyc = 0
        self.start_cyc = 0
        self.rw_table = None
        self.rw_table_list = None

        for idx,sig_name in enumerate(self.sig_dict["ff"]):
            self.sigid_2_signame[str(idx)] = sig_name
            self.signame_2_sigid[sig_name] = idx

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
                rw_row[rw_event["r"]] = {"w":set([w_event for w_event in rw_event["w"]]), "stay":set([w_event for w_event in rw_event["stay"]]), "ctrl":set([w_event for w_event in rw_event["ctrl"]]), "start_cyc":rw_event["start_cyc"], "end_cyc":rw_event["end_cyc"]}
            self.rw_table_list.append(rw_row)


        print("rw table loaded")
    

    def _get_all_fault_list(self):
        self.all_fault_list = {}
        for cyc in range(self.start_cyc, self.start_cyc+self.total_cyc ):
            for idx,sig_name in enumerate(self.sig_dict["ff"]):
                width = self.sig_dict["ff"][sig_name]
                self.all_fault_list[(cyc, idx)] = [bit_pos for bit_pos in range(width)]

    def _get_ace_fault_list(self):
        self.data_fault_list = {}
        self.ctrl_fault_list = {}
        data_fault_num = 0
        ctrl_fault_num = 0
        for idx, rw_row in enumerate(self.rw_table_list):
            cyc = idx + self.start_cyc
            for r_event in rw_row:
                width = self.sig_dict["ff"][r_event]
                idx = self.signame_2_sigid[r_event]
                if len(rw_row[r_event]["ctrl"]) > 0:
                    start_cyc = rw_row[r_event]["start_cyc"]
                    end_cyc = rw_row[r_event]["end_cyc"]
                    duration = end_cyc - start_cyc + 1
                    # Appending Fault List
                    self.ctrl_fault_list[(cyc, idx, duration)] = [bit for bit in range(width)]
                    ctrl_fault_num += width
                elif len(rw_row[r_event]["w"]) == 0:
                    continue
                else:
                    start_cyc = rw_row[r_event]["start_cyc"]
                    end_cyc = rw_row[r_event]["end_cyc"]
                    duration = end_cyc - start_cyc + 1

                    # Appending Fault List
                    self.data_fault_list[(cyc, idx, duration)] = [bit for bit in range(width)]
                    data_fault_num += width

        print(f"ace fault list obtained")
        print(f"total data fault injection = {data_fault_num}")
        print(f"total ctrl fault injection = {ctrl_fault_num}")

    def setup(self):
        #self._get_all_fault_list()
        self._get_ace_fault_list()


class FaultInjection(GenFaultList):
    def __init__(self,sigtable_dir:str, hw_dir:str, ace_dir:str, fi_name:str="fi_sim_veri"):
        GenFaultList.__init__(self,sigtable_dir,ace_dir)
        self.hw_dir = hw_dir
        self.fi_name = fi_name
        self.fsim_exe_file = f"{self.fi_name} > fsim.log"


    def fault_inject(self, cyc, idx, bit):
        f = open(self.hw_dir+"/control.txt","w")
        f.write(f"{cyc}\n{idx}\n{bit}")
        f.close()
        os.system(self.fsim_exe_file)

    
    def execute(self,mode):
        self.run_fault_sim(mode)
        self.bit_result_stat(mode)



    def run_fault_sim(self,mode:str):
        if mode == "total":
            self._get_all_fault_list()
            tot = len(self.all_fault_list)
            fault_list = self.all_fault_list
        else:
            self._get_ace_fault_list()
            if mode == "data":
                tot = len(self.data_fault_list)
                fault_list = self.data_fault_list
            elif mode == "ctrl":
                tot = len(self.ctrl_fault_list)
                fault_list = self.ctrl_fault_list
            else:
                raise
        
        #pprint.pp(list(self.data_fault_list.keys()))
        
        print("[Progress] running fault injection...")
        with tqdm(total=tot) as pbar:
            for cyc, idx, dura in fault_list.keys():
                for bit in fault_list[(cyc, idx, dura)]:
                    self.fault_inject(cyc, idx, bit)
                pbar.update(1)
        print("fault injection done.")


    def get_faulty_val(self, cyc, idx, bit):
        # Read faulty bit
        f = open(f"{self.hw_dir}/result/result_C{cyc:07}_R{idx:04}_B{bit:04}.txt","r")
        faulty_values = f.read().split("\n")
        f.close()
        return faulty_values

    def get_golden_val(self, cyc, idx, bit):
        # Read golden value for unknown elimination
        f = open(f"{self.hw_dir}/golden_value/golden_value_C{cyc+1:07}.txt")
        golden_values = f.read().split("\n")
        f.close()
        return golden_values

    def get_fault_list(self, mode:str):
        if mode == "total":
            fault_list = self.all_fault_list
        elif mode == "data":
            fault_list = self.data_fault_list
        elif mode == "ctrl":
            fault_list = self.ctrl_fault_list
        else:
            raise
        return fault_list

    def observe(self, faulty_values, golden_values, dst_reg_dict):
        dst_bit_list = []
        for idx, sig_name in enumerate(self.sig_dict["ff"]):
            width = len(faulty_values[idx])
            if len(faulty_values[idx]) != int(self.sig_dict["ff"][sig_name]):
                raise RTLFSimulationError("Error: Width Not Match.",1)
            else:
                prop_flag = False
                for c_idx in range(width):
                    if golden_values[idx][width-1-c_idx] == "x":
                        continue
                    if faulty_values[idx][width-1-c_idx] == "1":
                        dst_bit_list.append(f"{sig_name}[{c_idx}]")
                        prop_flag = True
                if prop_flag:
                    if sig_name in dst_reg_dict:
                        dst_reg_dict[sig_name] += 1
                    else:
                        dst_reg_dict[sig_name] = 1
        return dst_bit_list



    def bit_result_stat(self, mode:str):
        # Dataframe columns
        df_bit = {"cycle":[],"src_bit":[],"dst_bit":[],"fault_effect":[],"equivalent_cyc":[]}
        df_reg = {"cycle":[],"src_reg":[],"width":[],"dst_reg":[],"equivalent_cyc":[]}

        print("[Progress] observing bit level fault effect...")
        
        # Get fault list
        fault_list = self.get_fault_list(mode)
        tot = len(fault_list)

        #pprint.pp(list(self.data_fault_list.keys()))

        with tqdm(total=tot) as pbar:
            for cyc, reg_idx, dura in fault_list.keys():
                src_reg_name = self.sigid_2_signame[str(reg_idx)]
                dst_reg_dict = {}
                width = self.sig_dict["ff"][src_reg_name]
                for bit in fault_list[(cyc, reg_idx, dura)]:
                    # Read faulty bit
                    faulty_values = self.get_faulty_val(cyc, reg_idx, bit)
                    # Read golden
                    golden_values = self.get_golden_val(cyc, reg_idx, bit)

                    # Observation of Fault Effect
                    dst_bit_list = self.observe(faulty_values, golden_values, dst_reg_dict)

                    # Data Content Appendding
                    df_bit["cycle"].append(cyc)
                    df_bit["src_bit"].append(f"{src_reg_name}[{bit}]")
                    df_bit["dst_bit"].append(dst_bit_list)
                    df_bit["equivalent_cyc"].append(dura)
                    if dst_bit_list == []:
                        df_bit["fault_effect"].append("masked")
                    elif len(dst_bit_list) == 1:
                        df_bit["fault_effect"].append("single")
                    else:
                        df_bit["fault_effect"].append("multiple")
                df_reg["cycle"].append(cyc)
                df_reg["src_reg"].append(src_reg_name)
                df_reg["width"].append(width)
                df_reg["dst_reg"].append(dst_reg_dict)
                df_reg["equivalent_cyc"].append(dura)
                pbar.update(1)


        df_bit = pd.DataFrame(df_bit)
        result_dir = f"{self.hw_dir}/fault_sim_result({mode})(bit).csv"
        df_bit.to_csv(result_dir)
        print(f"Dumped <{result_dir}>")
        df_reg = pd.DataFrame(df_reg)
        result_dir = f"{self.hw_dir}/fault_sim_result({mode})(reg).csv"
        df_reg.to_csv(result_dir)
        print(f"Dumped <{result_dir}>")


                            

if __name__ == "__main__":
    # Step 1: Create the parser
    parser = argparse.ArgumentParser(description="A simple example of argparse usage.")

    # Step 2: Define arguments
    parser.add_argument("-m",'--mode', type=str, help="fault injection mode [total, data, ctrl]")
    parser.add_argument("-t",'--rwtable_dir', type=str, help="rw-table directory")
    parser.add_argument("-d",'--hw_dir', type=str, help="hardware directory")
    parser.add_argument("-f", "--fi_name", type=str, help="fault simulator directory")                  # Positional argument
    parser.add_argument("-s", "--sigtable_dir", type=str, help="signal table directory")

    # Step 3: Parse the arguments
    args = parser.parse_args()

    inj = FaultInjection(
              sigtable_dir = args.sigtable_dir, 
              hw_dir = args.hw_dir, 
              ace_dir = args.rwtable_dir, 
              fi_name = args.fi_name
          )

    inj.execute(args.mode)
