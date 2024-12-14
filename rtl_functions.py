from exceptions import SimulationError

def _and(lv:str,rv:str):
    rv = rv.replace("z","x")
    lv = lv.replace("z","x")
    if rv+lv == "xx":
        return "x"
    elif "x" in rv+lv:
        if "0" in rv+lv:
            return "0"
        else:
            return "x"
    else:
        return "1"

def _or(lv:str,rv:str):
    rv = rv.replace("z","x")
    lv = lv.replace("z","x")
    if rv+lv == "xx":
        return "x"
    elif "x" in rv+lv:
        if "1" in rv+lv:
            return "1"
        else:
            return "x"
    else:
        return "0"

def _xor(lv:str,rv:str):
    rv = rv.replace("z","x")
    lv = lv.replace("z","x")
    if "x" in rv+lv:
        return "x"
    else:
        if rv == lv:
            return "0"
        else:
            return "1"

def _not(v:str):
    v = v.replace("z","x")
    if v == "x":
        return "x"
    else:
        if v == "1":
            return "0"
        else:
            return "1"

def _half_add(self,lv,rv,carry):
    if "x" in lv+rv+carry:
        if (lv+rv+carry).find("1") == 0:
            new_carry = "0"
        elif (lv+rv+carry).find("1") == 1:
            new_carry = "x"
        elif (lv+rv+carry).find("1") > 1:
            new_carry = "1"
        result = "x"
    else:
        if (lv+rv+carry).find("1")%2 == 1:
            result = "1"
        else:
            result = "0"
        if (lv+rv+carry).find("1") > 1:
            new_carry = "1"
        else:
            new_carry = "0"
    return result, new_carry

# computation part
def val_and(lv:str,rv:str,width:int):
    result = ""
    for idx in range(width):
        result = result + _and(rv[idx],lv[idx])
    return result

def val_or(lv:str,rv:str,width:int):
    result = ""
    for idx in range(width):
        result = result + _or(rv[idx],lv[idx])
    return result

def val_xor(lv:str,rv:str,width:int):
    result = ""
    for idx in range(width):
        result = result + _xor(rv[idx],lv[idx])
    return result

def val_not(iv:str):
    result = ""
    width = len(iv)
    for idx in range(width):
        result = result + _not(iv[idx])
    return result


def val_shiftl(lv:str,rv:str,width:int):
    if "x" in rv:
        result = "x"*width
    else:
        offset = int(rv,2)
        result = lv[offset:] + "0"*offset
    return result

def val_shiftr(lv:str,rv:str,width:int):
    if "x" in rv:
        result = "x"*width
    else:
        offset = int(rv,2)
        result = "0"*offset + lv[:-(offset)]
    return result

def val_shiftrs(lv:str,rv:str,width:int):
    if "x" in rv:
        result = "x"*width
    else:
        offset = int(rv,2)
        result = lv[0]*offset + lv[:-(offset)]
    return result

def val_add(lv:str,rv:str,width:int):
    if "x" in lv+rv:
        return "x"*width
    if rv[0] == "1":
        rv = "-0b"+rv
    if lv[0] == "1":
        lv = "-0b"+lv
    result = int(rv, 2) + int(lv, 2)
    result = f"{result:0{width}b}"
    result = format(result & int("1"*width,2),f"{width}b")
    return result

def val_sub(lv:str,rv:str,width:int):
    if "x" in lv+rv:
        return "x"*width
    if rv[0] == "1":
        rv = "-0b"+rv
    if lv[0] == "1":
        lv = "-0b"+lv
    result = int(rv, 2) - int(lv, 2)
    result = f"{result:0{width}b}"
    #result = format(result & int("1"*width,2),f"{width}b")
    return result

def val_muls(lv:str,rv:str,width:int):
    if "x" in lv+rv:
        return "x"*width
    if rv[0] == "1":
        rv = "-0b"+rv
    if lv[0] == "1":
        lv = "-0b"+lv
    result = int(rv, 2) * int(lv, 2)
    result = f"{result:0{width}b}"
    #result = format(result & int("1"*width,2),f"{width}b")
    return result

def val_eq(lv:str,rv:str):
    if rv == lv:
        return "1"
    else:
        return "0"

def val_neq(lv:str,rv:str):
    if rv != lv:
        return "1"
    else:
        return "0"

def val_gt(lv:str,rv:str):
    for idx in range(width):
        if lv[idx]+rv[idx] == "10":
            return "1"
        elif "x" in lv[idx]+rv[idx]:
            return "x"
    return "0"

def val_lt(lv:str,rv:str):
    width = len(lv)
    for idx in range(width):
        if lv[idx]+rv[idx] == "01":
            return "1"
        elif "x" in lv[idx]+rv[idx]:
            return "x"
    return "0"

def val_gte(lv:str,rv:str):
    lt = val_lt(lv,rv)
    if lt == "x":
        return "x"
    elif lt == "1":
        return "0"
    else:
        return "1"


def val_lte(lv:str,rv:str):
    gt = val_gt(lv,rv)
    if gt == "x":
        return "x"
    elif gt == "1":
        return "0"
    else:
        return "1"



def val_gts(lv:str,rv:str):
    pass

def val_lts(lv:str,rv:str):
    pass

def val_gtes(lv:str,rv:str): 
    lts = val_lts(lv,rv)
    if lts == "x":
        return "x"
    elif lts == "1":
        return "0"
    else:
        return "1"
def val_ltes(lv:str,rv:str):
    gts = val_gts(lv,rv)
    if gts == "x":
        return "x"
    elif gts == "1":
        return "0"
    else:
        return "1"

def val_concat(lv:str,rv:str):
    return lv+rv

def val_redor(v:str):
    if "1" in v:
        return "1"
    else:
        if "x" in v:
            return "x"
        else:
            return "0"

def val_redand(v:str):
    if "0" in v:
        return "0"
    else:
        if "x" in v:
            return "x"
        else:
            return "1"

def val_extend(v:str,width:int):
    delta = width - len(v)
    return ("0" * delta) + v
def val_extends(v:str,width:int):
    delta = width - len(v)
    return (v[0] * delta) + v


def val_1_op(node):
    width = node.width
    i_value = node.children[0].value
    i_value = i_value.replace("z","x")
    if node.tag == "not":
        result = val_not(i_value)
    elif node.tag == "extend":
        result = val_extend(i_value,width)
    elif node.tag == "extends":
        result = val_extends(i_value,width)
    elif node.tag == "redor":
        result = val_redor(i_value)
    elif node.tag == "redand":
        result = val_redand(i_value)
    else:
        raise SimulationError(f"Unknown op to compute: tag = {node.tag}.",2)
    return result


def val_2_op(node):
    width = node.width
    r_value = node.children[0].value
    l_value = node.children[1].value
    r_value = r_value.replace("z","x")
    l_value = l_value.replace("z","x")
    if node.tag == "and":
        result = val_and(l_value,r_value,width)
    elif node.tag == "or":
        result = val_or(l_value,r_value,width)
    elif node.tag == "xor":
        result = val_xor(l_value,r_value,width)
    elif node.tag == "add":
        result = val_add(l_value,r_value,width)
    elif node.tag == "sub":
        result = val_sub(l_value,r_value,width)
    elif node.tag == "muls":
        result = val_muls(l_value,r_value,width)
    elif node.tag == "shiftl":
        result = val_shiftl(l_value,r_value,width)
    elif node.tag == "shiftr":
        result = val_shiftr(l_value,r_value,width)
    elif node.tag == "shiftrs":
        result = val_shiftrs(l_value,r_value,width)
    elif node.tag == "eq":
        result = val_eq(l_value,r_value)
    elif node.tag == "neq":
        result = val_neq(l_value,r_value)
    elif node.tag == "gt":
        result = val_gt(l_value,r_value)
    elif node.tag == "gte":
        result = val_gte(l_value,r_value)
    elif node.tag == "lte":
        result = val_lte(l_value,r_value)
    elif node.tag == "lt":
        result = val_lt(l_value,r_value)
    elif node.tag == "lts":
        result = val_lts(l_value,r_value)
    elif node.tag == "concat":
        result = val_concat(l_value,r_value)
    else:
        raise SimulationError(f"Unknown op to compute: tag = {node.tag}.",1)

    return result

