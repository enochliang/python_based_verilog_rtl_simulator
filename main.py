from config_benchmark import configs
from gen_make import GenMakefile
import os

if __name__ == "__main__":
    for conf in configs:
        config = configs[conf]

        gen = GenMakefile(
            design_name=config["design_name"],
            start_cyc=config["start_cyc"],
            period=config["period"],
            pysim_mode=config["pysim_mode"],
        )
        gen.generate()
        with open("Makefile","w") as fp:
            fp.write(gen.makefile)
        os.system("make pyfsim")

