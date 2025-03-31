import dataloader
import argparse
import json

class CtrlReduceAnalysis:
    def __init__(self,rw_table_dir:str, rw_table_ctrl_dir:str):
        rw_load = dataloader.rw_table(rw_table_dir)
        self.rw_table  = rw_load["rw_table_list"]
        self.tot_cyc   = rw_load["total_cyc"]
        self.start_cyc = rw_load["start_cyc"]

        rw_load = dataloader.rw_table(rw_table_ctrl_dir)
        self.rw_table_ctrl = rw_load["rw_table_list"]

    def compare(self):
        start    = self.start_cyc
        tot      = self.tot_cyc
        rw_tab   = self.rw_table
        rw_tab_c = self.rw_table_ctrl
        reduced_link = 0
        masked = 0
        total_ctrl_link = 0
        total_ctrl_link_red = 0
        total_data_link = 0
        for cyc in range(tot):
            rw_evts_c = rw_tab_c[cyc]
            rw_evts = rw_tab[cyc]
            for src in rw_evts_c:
                ctrl_w_events_c = set([ctrl_w_events_c[0] for ctrl_w_events_c in rw_evts_c[src]["ctrl"] ])
                if src in rw_evts:
                    ctrl_w_events   = set([ctrl_w_events[0] for ctrl_w_events in rw_evts[src]["ctrl"] ])
                    w_events   = set([ctrl_w_events[0] for ctrl_w_events in rw_evts[src]["w"] ])
                    total_data_link += len(w_events)
                    diff_num = len(ctrl_w_events_c ^ ctrl_w_events)
                else:
                    diff_num = len(ctrl_w_events_c)
                    masked += 1
                total_ctrl_link_red += len(ctrl_w_events)
                total_ctrl_link += len(ctrl_w_events_c)
                reduced_link += diff_num
        print(f"The Number of Total Data Links = {total_data_link}")
        print(f"The Number of Total Control Links = {total_ctrl_link}")
        print(f"The Number of Control Links after Reduction = {total_ctrl_link_red}")
        print(f"The Number of Reduced Links = {reduced_link}")
        print(f"The Number of Additional Masked = {masked}")
        output = {"total_ctrl_link": total_ctrl_link,
                  "total_ctrl_link_red": total_ctrl_link_red,
                  "total_data_link": total_data_link
                }
        return output

if __name__ == "__main__":
    # Step 1: Create the parser
    parser = argparse.ArgumentParser(description="A simple example of argparse usage.")

    # Step 2: Define arguments
    parser.add_argument('--design_dir', type=str, help="design dir")
    parser.add_argument('--rw_table_dir', type=str, help="RW Table dir")
    parser.add_argument('--rw_table_c_dir', type=str, help="RW Table without Ctrl Reduction dir")

    # Step 3: Parse the arguments
    args = parser.parse_args()

    design_dir = args.design_dir
    rw_table_dir = args.rw_table_dir
    rw_table_ctrl_dir = args.rw_table_c_dir
    comp = CtrlReduceAnalysis(rw_table_dir, rw_table_ctrl_dir)
    output = comp.compare()
    with open(design_dir+"/reduced_path.json","w") as fp:
        json.dump(output, fp)




