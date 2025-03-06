if [ -d ".venv" ]; then
    echo "Checking Python version in .venv..."
    PYTHON_VERSION=$(.venv/bin/python --version 2>&1)
    REQUIRED_VERSION="3.7"

    # Extract the major and minor version using awk
    INSTALLED_VERSION=$(echo "$PYTHON_VERSION" | awk '{print $2}' | awk -F. '{print $1"."$2}')

    # Compare versions using sort -V. If the lower of the two is the required version,
    # then INSTALLED_VERSION is greater than or equal to REQUIRED_VERSION.
    if [ "$(printf '%s\n' "$INSTALLED_VERSION" "$REQUIRED_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then
        echo "Activating .venv: Python $INSTALLED_VERSION (>= $REQUIRED_VERSION) found."
        source .venv/bin/activate
        pytest -s -v --log-cli-level=DEBUG --capture=tee-sys tests/
    else
        echo "Error: Python version $INSTALLED_VERSION in .venv is less than required $REQUIRED_VERSION."
        exit 1
    fi
else
    echo "Error: .venv not found. Please create a virtual environment."
    exit 1
fi


pytest -s -v --log-cli-level=DEBUG --capture=tee-sys tests/