class AstNodeClassify:
    def __init__(self):
        
        # OPs
        self.arith_op__negate = {"negate"}
        self.arith_op__uncomm = {"sub"}
        self.arith_op__comm = {"add","mul","muls"}
        self.arith_op__shift = {"shiftrs","shiftr","shiftl"}
        self.arith_op__general = self.arith_op__uncomm | self.arith_op__comm
        self.arith_op__logic_2_port__pass = {"xor"}
        self.arith_op__logic_2_port__mask = {"and", "or"}
        self.arith_op__logic_2_port = self.arith_op__logic_2_port__pass | self.arith_op__logic_2_port__mask
        self.arith_op__logic_1_port = {"not"}
        self.arith_op__2_port = self.arith_op__uncomm | self.arith_op__comm | self.arith_op__shift | self.arith_op__logic_2_port
        self.arith_op__1_port = self.arith_op__logic_1_port | self.arith_op__negate
        self.arith_op = self.arith_op__2_port | self.arith_op__1_port

        self.logic_op__red = {"redand", "redor", "redxor"}
        self.logic_op__log = {"logand","logor"}
        self.logic_op = self.logic_op__red | self.logic_op__log

        self.comp_op__eq = {"eq", "neq"}
        self.comp_op__neq = {"gt", "gte", "lt", "lte"}
        self.comp_op__neqs = {"gts", "gtes", "lts", "ltes"}
        self.comp_op = self.comp_op__eq | self.comp_op__neq | self.comp_op__neqs

        self.reg_manip_op__merge = {"concat"}
        self.reg_manip_op__extend = {"extend","extends"}
        self.reg_manip_op__replicate = {"replicate"}
        self.reg_manip_op = self.reg_manip_op__merge | self.reg_manip_op__extend | self.reg_manip_op__replicate

        self.cond_op = {"cond"}
        self.const_node = {"const"}

        self.always_prop_op = self.arith_op__uncomm | self.arith_op__comm | self.arith_op__logic_1_port | self.arith_op__logic_2_port__pass | self.reg_manip_op

        self.op__2_port = self.arith_op__2_port | self.logic_op__log | self.comp_op | self.reg_manip_op__merge | self.reg_manip_op__replicate
        self.op__1_port = self.arith_op__1_port | self.logic_op__red | self.reg_manip_op__extend


