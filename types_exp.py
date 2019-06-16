import typing


def test(x: str) -> typing.List[int]:
    print(x)
    return [2, 3]


if __name__ == '__main__':
    test(3)
