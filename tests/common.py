from collections import namedtuple
from py_ecc.bn128 import G1, multiply, add
from zkevm_specs.util import random_bn128_point, to_cf_form

SASSY_AB_VALUES = (
    (G1, random_bn128_point()),
    (None, random_bn128_point()),
    (random_bn128_point(), None),
    (random_bn128_point(), random_bn128_point()),
)

NASTY_AB_VALUES = (
    (0, 0),
    (1, 0),
    (0, 1),
    (1, 1),
    (255, 0),
    (0, 255),
    (255, 255),
    (256, 0),
    (0, 256),
    (256, 256),
    (260, 513),
    (65535, 0),
    (0, 65535),
    (65535, 65535),
    (65536, 0),
    (0, 65536),
    (65536, 65536),
    ((1 << 256) - 1, (1 << 256) - 2),
    ((1 << 256) - 2, (1 << 256) - 1),
    ((1 << 256) - 1, 0),
    (0, (1 << 256) - 1),
)

PrecompileCallContext = namedtuple(
    "PrecompileCallContext",
    [
        "is_root",
        "is_create",
        "program_counter",
        "stack_pointer",
        "gas_left",
        "memory_size",
        "reversible_write_counter",
    ],
    defaults=[True, False, 232, 1023, 0, 0, 0],
)


def generate_sassy_tests():
    input_length = 128
    point_length = 64

    tests = []
    for point_a, point_b in SASSY_AB_VALUES:
        point_c = add(point_a, point_b)

        a = to_cf_form(point_a)
        b = to_cf_form(point_b)
        c = to_cf_form(point_c)
        ma = a.marshal()
        mb = b.marshal()
        mc = c.marshal()

        input = ma + mb
        result = mc

        tests.append((PrecompileCallContext(), 0, input_length, 0, point_length, input, result))

    return tests


def generate_nasty_tests(tests, opcodes):
    for opcode in opcodes:
        for a, b in NASTY_AB_VALUES:
            tests.append((opcode, a, b))
