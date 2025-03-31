configs = {
        "picorv32_basicmath":{
            "python_cmd":"python3",
            "design_folder":"picorv32/benchmark_basicmath",
            "top_module_name":"picorv32",
            "tb_clk":"clk",
            "tb_rst":"resetn",
            "top_hier":"uut",
            "min_cyc":5,
            "max_cyc":2675
        },
        "picorv32_qsort":{
            "python_cmd":"python3",
            "design_folder":"picorv32/benchmark_qsort",
            "top_module_name":"picorv32",
            "tb_clk":"clk",
            "tb_rst":"resetn",
            "top_hier":"uut",
            "min_cyc":5,
            "max_cyc":5971295
        },
        "picorv32_string":{
            "python_cmd":"python3",
            "design_folder":"picorv32/benchmark_string",
            "top_module_name":"picorv32",
            "tb_clk":"clk",
            "tb_rst":"resetn",
            "top_hier":"uut",
            "min_cyc":5,
            "max_cyc":14752
        },
        "picorv32_stencil":{
            "python_cmd":"python3",
            "design_folder":"picorv32/benchmark_stencil",
            "top_module_name":"picorv32",
            "tb_clk":"clk",
            "tb_rst":"resetn",
            "top_hier":"uut",
            "min_cyc":5,
            "max_cyc":590000
        },
        "picorv32_firmware":{
            "python_cmd":"python3",
            "design_folder":"picorv32/benchmark_firmware",
            "top_module_name":"picorv32_axi",
            "tb_clk":"clk",
            "tb_rst":"resetn",
            "top_hier":"top.uut",
            "min_cyc":5,
            "max_cyc":388059
        },
        "picorv32_dhrystone":{
            "python_cmd":"python3",
            "design_folder":"picorv32/benchmark_dhrystone",
            "top_module_name":"picorv32",
            "tb_clk":"clk",
            "tb_rst":"resetn",
            "top_hier":"top.uut",
            "min_cyc":5,
            "max_cyc":371627
        },
        "aes":{
            "python_cmd":"python3",
            "design_folder":"aes",
            "top_module_name":"aes_core",
            "tb_clk":"tb_clk",
            "tb_rst":"tb_reset_n",
            "top_hier":"tb_aes_core.dut",
            "min_cyc":5,
            "max_cyc":244
        },
        "sha1":{
            "python_cmd":"python3",
            "design_folder":"sha1",
            "top_module_name":"sha1_core",
            "tb_clk":"tb_clk",
            "tb_rst":"tb_reset_n",
            "top_hier":"tb_sha1_core.dut",
            "min_cyc":5,
            "max_cyc":244
        },
        "FFTx32":{
            "python_cmd":"python3",
            "design_folder":"FFTx32/src",
            "top_module_name":"FFT",
            "tb_clk":"clk",
            "tb_rst":"rst_n",
            "top_hier":"FFT_CORE",
            "min_cyc":5,
            "max_cyc":80
        },
        "vSPI":{
            "python_cmd":"python3",
            "design_folder":"vSPI",
            "top_module_name":"spiifc",
            "tb_clk":"SysClk",
            "tb_rst":"Reset",
            "top_hier":"spiifc_tb2.uut",
            "min_cyc":5,
            "max_cyc":225
        },
        "tinyriscv_qsort":{
            "python_cmd":"python3",
            "design_folder":"tinyriscv/benchmark_qsort",
            "top_module_name":"tinyriscv",
            "tb_clk":"clk",
            "tb_rst":"rst",
            "top_hier":"tinyriscv_soc_tb.tinyriscv_soc_top_0.u_tinyriscv",
            "min_cyc":5,
            "max_cyc":669847
        },
        "tinyriscv_median":{
            "python_cmd":"python3",
            "design_folder":"tinyriscv/benchmark_median",
            "top_module_name":"tinyriscv",
            "tb_clk":"clk",
            "tb_rst":"rst",
            "top_hier":"tinyriscv_soc_tb.tinyriscv_soc_top_0.u_tinyriscv",
            "min_cyc":5,
            "max_cyc":51448
        },
        "tinyriscv_towers":{
            "python_cmd":"python3",
            "design_folder":"tinyriscv/benchmark_towers",
            "top_module_name":"tinyriscv",
            "tb_clk":"clk",
            "tb_rst":"rst",
            "top_hier":"tinyriscv_soc_tb.tinyriscv_soc_top_0.u_tinyriscv",
            "min_cyc":5,
            "max_cyc":29951
        },
        "tinyriscv_vvadd":{
            "python_cmd":"python3",
            "design_folder":"tinyriscv/benchmark_vvadd",
            "top_module_name":"tinyriscv",
            "tb_clk":"clk",
            "tb_rst":"rst",
            "top_hier":"tinyriscv_soc_tb.tinyriscv_soc_top_0.u_tinyriscv",
            "min_cyc":5,
            "max_cyc":29707
        },
        "tinyriscv_multiply":{
            "python_cmd":"python3",
            "design_folder":"tinyriscv/benchmark_multiply",
            "top_module_name":"tinyriscv",
            "tb_clk":"clk",
            "tb_rst":"rst",
            "top_hier":"tinyriscv_soc_tb.tinyriscv_soc_top_0.u_tinyriscv",
            "min_cyc":5,
            "max_cyc":101996
        },
        "tinyriscv_rsort":{
            "python_cmd":"python3",
            "design_folder":"tinyriscv/benchmark_rsort",
            "top_module_name":"tinyriscv",
            "tb_clk":"clk",
            "tb_rst":"rst",
            "top_hier":"tinyriscv_soc_tb.tinyriscv_soc_top_0.u_tinyriscv",
            "min_cyc":5,
            "max_cyc":852456
        }
    }
