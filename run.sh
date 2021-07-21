export PYTHONPATH=$PYTHONPATH:pgi

# Check if the script is working
python pgi/dtip/dtip.py --help

# Create a requirements files
pip list --format=freeze > requirements.txt

# install pgi package with editable mode
pip install --editable .