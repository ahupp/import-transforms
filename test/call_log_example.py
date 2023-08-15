def top():
    return middle(1)


def middle(value):
    return bottom(value + 2)


def bottom(value):
    return value + 3


top()
