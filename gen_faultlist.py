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
