"""
Based on pymtl/pymtl/tools/translation/verilator_to_pymtl.py
"""

import sys
import os
import jinja2

VERILATOR_INCLUDE_DIR = '/usr/share/verilator/include'


def verilog_to_python(model_name, filename_v, in_ports, out_ports, working_directory):
    """
    Create a python interface for Verilog HDL.
    """
    filename_pyx = model_name + '.pyx'
    vobj_name = 'V' + model_name
    print('verilating model')
    verilate_model(filename_v, model_name)
    print('creating cython')
    create_cython(in_ports, out_ports, model_name, filename_pyx, vobj_name, working_directory)
    create_setup(filename_pyx, vobj_name, model_name)
    cythonize_model(model_name)


def verilate_model(filename, model_name):
    cmd = ('rm -r obj_dir_{1}; verilator -cc {0} -top-module {1}'
           ' --Mdir obj_dir_{1} -trace -Wno-lint -Wno-UNOPTFLAT').format(filename, model_name)
    print(cmd)
    os.system(cmd)


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


def create_cython(in_ports, out_ports, model_name, filename_pyx, vobj_name, working_directory):
    """
    Generate a Cython wrapper file for Verilated C++.
    """
    # Generate the Cython source code
    template_fn = 'template.pyx'
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


def create_setup( filename_pyx, vobj_name, model_name ):
    """
    Create a setup.py file to compile the Cython Verilator wrapper.
    """
    # Generate setup.py
    verilator_include = VERILATOR_INCLUDE_DIR
    dir_ = 'obj_dir_{0}'.format( model_name )
    file_ = '"{0}/{{}}",'.format(dir_)
    sources = [file_.format(x) for x in os.listdir(dir_) if '.cpp' in x]
    sources = ' '.join(sources)

    f = open('setup_{0}.py'.format(model_name), 'w')

    f.write( "from distutils.core import setup\n"
            "from distutils.extension import Extension\n"
            "from Cython.Distutils import build_ext\n"
            "\n"
            "setup(\n"
            "  ext_modules = [ Extension( '{0}',\n"
            "                             sources=['{1}',\n"
            "                             {5}\n"
            "                             '{4}/verilated.cpp',"
            "                             '{4}/verilated_vcd_c.cpp'"
            "                             ],\n"
            "                             include_dirs=['{4}'],\n"
            "                             language='c++' ) ],\n"
            "  cmdclass = {2}'build_ext': build_ext{3}\n"
            ")\n".format(vobj_name, filename_pyx, '{', '}', verilator_include, sources))
    f.close()


def cythonize_model( model_name ):
    """
    Create a Python interface to the Verilated C++ using Cython.
    """
    os.system('python setup_{0}.py build_ext -i -f'.format(model_name))
