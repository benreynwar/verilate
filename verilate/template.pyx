cdef extern from 'verilated_vcd_c.h':
    cdef cppclass VerilatedVcdC:
        void open(char*)
        void dump(int)
        void close()

cdef extern from '{{obj_dir}}/V{{top}}.h':
    cdef cppclass V{{top}}:{% for port_name, mangled_name, (port_c_type, port_array_size), port_width in ports %}
        {{port_c_type}} {{mangled_name}}{% if port_array_size %}[{{port_array_size}}]{% endif %}{% endfor %}
        void eval()
        void trace(VerilatedVcdC*, int)

cdef extern from 'verilated.h' namespace 'Verilated':
    void traceEverOn(bool)

def XTraceEverOn():
    traceEverOn(1)

cdef class Wrapped:
    cdef V{{top}}* wrapped
    cdef VerilatedVcdC* tfp
    cdef int main_time

    def __cinit__(self):
        self.wrapped = new V{{top}}()
        self.tfp = new VerilatedVcdC()
        self.main_time = 0
        self.wrapped.trace(self.tfp, 99)
        self.tfp.open('vlt_dump.vcd')

    def __dealloc__(self):
        if self.wrapped:
            del self.wrapped
        if self.tfp:
            self.tfp.close()
            del self.tfp

    def dump(self):
        self.main_time = self.main_time + 1
        self.tfp.dump(self.main_time)

    @property
    def the_time(self):
        return self.main_time

    @the_time.setter
    def the_time(self, time):
        self.main_time = time

    {% for port_name, mangled_name, port_c_type, port_width in ports %}
    @property
    def {{port_name}}(self):
        {% if port_width <= 64 %}return self.wrapped.{{mangled_name}}{% else %}port_width = {{port_width}}
        word_size = 32
        value = 0
        for word_index in range((port_width-1)//word_size, -1, -1):
            value = (value << word_size) + self.wrapped.{{mangled_name}}[word_index]
        return value
        {% endif %}
    {% endfor %}
        
    {% for port_name, mangled_name, port_c_type, port_width in in_ports %}
    @{{port_name}}.setter
    def {{port_name}}(self, value):
        {% if port_width <= 64 %}self.wrapped.{{mangled_name}} = value{% else %}port_width = {{port_width}}
        word_size = 32
        f  = pow(2, word_size)
        for word_index in range((port_width-1)//word_size+1):
            word = value % f
            value = value >> word_size
            self.wrapped.{{mangled_name}}[word_index] = word
        {% endif %}
    {% endfor %}

    def eval(self):
      self.wrapped.eval()
