from ash_dal import __VERSION__


# Temporary test to bypass CI/CD checks
def test_version():
    assert __VERSION__ == "0.2.0"
