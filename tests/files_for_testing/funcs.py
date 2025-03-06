"""
This file should only have functions for testing.

classes.py holds classes
funcs_and_classes.py holds a mix of them.
"""


def simple_printer():
    for i in range(1, 6):
        print('*' * i)


def idk():
    for i in range(1, 6):
        print(' '.join(str(j) for j in range(1, i + 1)))


def probably_asterisks_and_spaces():
    for i in range(1, 6):
        print(' ' * (5 - i) + '*' * (2 * i - 1))
    for i in range(4, 0, -1):
        print(' ' * (5 - i) + '*' * (2 * i - 1))


def probably_zigzag():
    width = 5
    height = 9

    for i in range(height):
        level = i % (width - 1)
        if (i // (width - 1)) % 2 == 1:
            level = (width - 1) - level
        print(' ' * level + '*')
