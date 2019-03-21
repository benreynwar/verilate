"""
Based on pymtl/pymtl/tools/translation/verilator_to_pymtl.py
"""

import sys
import os
import jinja2
import subprocess
import glob

VERILATOR_INCLUDE_DIR = '/usr/share/verilator/include'

THIS_DIR = os.path.dirname(__file__)


def verilog_to_python(model_name, filename_v, in_ports, out_ports, working_directory):
    """
    Create a python interface for Verilog HDL.
    """
    working_directory = os.path.abspath(working_directory)
    filename_pyx = os.path.join(working_directory, model_name + '.pyx')
    vobj_name = 'V' + model_name
    print('verilating model')
    obj_directory = os.path.join(working_directory, 'obj_dir_' + model_name)
    # Call verilator
    subprocess.call(['verilator', '-cc', filename_v, '-top-module', model_name,
                     '--Mdir', obj_directory, '-trace', '-Wno-lint', '-Wno-UNOPTFLAT'])
    print('creating cython')
    create_cython(in_ports, out_ports, model_name, filename_pyx, working_directory)
    setup_filename = os.path.join(working_directory, 'setup_{}.py'.format(model_name))
    create_setup(filename_pyx, vobj_name, model_name, setup_filename, obj_directory)
    subprocess.call(['python', setup_filename, 'build_ext', '-i', '-f'], cwd=working_directory)
    sys.path.append(working_directory)


def get_type(width):
    if width <= 8:
        return ('char', None)
    elif width <= 16:
        return ('unsigned short', None)
    elif width <= 32:
        return ('unsigned long', None)
    elif width <= 64:
        return ('long long', None)
    else:
        return ('unsigned long', (width-1)//32+1)


def mangle_name(name):
    return name.replace('__', '___05F')


def create_cython(in_ports, out_ports, model_name, filename_pyx, working_directory):
    """
    Generate a Cython wrapper file for Verilated C++.
    """
    # Generate the Cython source code
    template_fn = os.path.join(THIS_DIR, 'template.pyx')
    with open(template_fn, 'r') as f:
        template = jinja2.Template(f.read())
    in_port_types = [
        (name, mangle_name(name), get_type(width), width) for name, width in in_ports]
    out_port_types = [
        (name, mangle_name(name), get_type(width), width) for name, width in out_ports]
    pyx_contents = template.render(
        top=model_name,
        ports=in_port_types+out_port_types,
        in_ports=in_port_types,
        out_ports=out_port_types,
        obj_dir=os.path.join(working_directory, 'obj_dir_{}'.format(model_name)),
        )
    with open(filename_pyx, 'w') as f:
        f.write(pyx_contents)

TEMPLATE_PYX = """
from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

setup(
  ext_modules=[
    Extension(
      'V{model_name}',
      sources=['{filename_pyx}',
                {sources},
               '{verilator_include}/verilated.cpp',
               '{verilator_include}/verilated_vcd_c.cpp',
      ],
      include_dirs=['{verilator_include}'],
      language='c++' ) ],
  cmdclass = {{'build_ext': build_ext}}
  )
"""

def create_setup(filename_pyx, vobj_name, model_name, setup_filename, obj_directory):
    """
    Create a setup.py file to compile the Cython Verilator wrapper.
    """
    content = TEMPLATE_PYX.format(
        model_name=model_name,
        filename_pyx=filename_pyx,
        verilator_include=VERILATOR_INCLUDE_DIR,
        sources=', '.join(["'{}'".format(x) for x in glob.glob(os.path.join(obj_directory, '*.cpp'))]),
        )
    with open(setup_filename, 'w') as f:
        f.write(content)
