from portfolio_starter.main import hello


def test_smoke() -> None:
    test_hello()


def test_hello() -> None:
    assert hello("world") == "Hello, world!"
