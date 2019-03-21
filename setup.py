import os
from setuptools import setup

setup(
    name = "verilate",
    packages=['verilate'],
    use_scm_version = {
        "relative_to": __file__,
        "write_to": "verilate/version.py",
    },
    author = "Ben Reynwar",
    author_email = "ben@reynwar.net",
    description = ("Helps with wrapping verilated verilog in python."),
    license = "MIT/BSD",
    keywords = ["VHDL", "verilog", "hdl", "rtl", "synthesis", "FPGA", "simulation", "Xilinx", "Altera"],
    url = "https://github.com/benreynwar/verilate",
    setup_requires=[
        'setuptools_scm',
    ],
    install_requires=[
        'cython',
    ],
)
