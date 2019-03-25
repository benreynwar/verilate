import random
import math

from verilate import verilator_cython


def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def fix_output_dict(outputs):
    if outputs is None:
        return None
    simple_outputs = {}
    grouped_outputs = {}
    for name, value in outputs.items():
        if '__' not in name:
            simple_outputs[name] = value
        else:
            split_name = name.split('__')
            if split_name[0] not in grouped_outputs:
                grouped_outputs[split_name[0]] = {}
            grouped_outputs[split_name[0]]['__'.join(split_name[1:])] = value
    for name, group in grouped_outputs.items():
        assert name not in simple_outputs
        simple_outputs[name] = fix_output_dict(group)
    keys = simple_outputs.keys()
    if all([is_int(k) for k in keys]):
        as_ints = [int(k) for k in keys]
        max_value = max(as_ints)
        final_outputs = [None] * (max_value+1)
        for key, value in simple_outputs.items():
            final_outputs[int(key)] = value
    else:
        final_outputs = simple_outputs
    return final_outputs


def set_value(wrapped, name, value):
    if isinstance(value, list):
        for index, piece in enumerate(value):
            set_value(wrapped, name + '__{}'.format(index), piece)
    elif isinstance(value, dict):
        for subname, piece in value.items():
            set_value(wrapped, name + '__{}'.format(subname), piece)
    else:
        setattr(wrapped, name, value)


def run_basic_test_with_verilator(wrapped, tb, clock_name='clk'):
    outputs = None
    while True:
        try:
            setattr(wrapped, clock_name, 0)
            inputs = tb.send(fix_output_dict(outputs))
            for signal_name, signal_value in inputs.items():
                set_value(wrapped, signal_name, signal_value)
            wrapped.eval()
            output_signal_names = []
            for key in dir(wrapped):
                if key[0] != '_' and key not in ('eval', 'dump', 'the_time', 'clk'):
                    output_signal_names.append(key)
            outputs = {}
            for output_signal_name in output_signal_names:
                outputs[output_signal_name] = getattr(wrapped, output_signal_name)
            setattr(wrapped, clock_name, 1)
            wrapped.eval()
        except StopIteration:
            break
