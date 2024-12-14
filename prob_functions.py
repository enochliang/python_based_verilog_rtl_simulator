
def prob_and(lv:str,rv:str,result:str):
    pass


def f_prop(l_f_list:dict,r_f_list:dict):
    f_list = {}
    for fault, prob in l_f_list.items():
        f_list_append(fault,prob,f_list)
    for fault, prob in r_f_list.items():
        f_list_append(fault,prob,f_list)
    return f_list

def f_list_append(fault,prob,f_list:dict):
    if fault in f_list:
        if f_list[fault] < prob:
            f_list[fault] = prob
    else:
        f_list[fault] = prob
