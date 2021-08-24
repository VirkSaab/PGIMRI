export PYTHONPATH=$PYTHONPATH:pgimri

# WX tools for jupyter notebook with FSL
# sudo apt-get install python-wxtools


# Check if the script is working
# python pgimri/dtip/dtip.py --help

# Create a requirements files
pip list --format=freeze > requirements.txt

# install pgi package with editable mode
pip install --editable .

# Make documentation
# Some sphinx error fixes:
# https://stackoverflow.com/questions/13516404/sphinx-error-unknown-directive-type-automodule-or-autoclass
sphinx-quickstart docs
cd docs
# sphinx-build -b html . build/html
sphinx-build -b html source/ build/html
# sphinx-apidoc -o . .. --force
sphinx-apidoc -o source/ ../pgimri
make html
# To automatically generate HTML updates: follow these instructions - https://sublime-and-sphinx-guide.readthedocs.io/en/latest/build.html#automatically-generate-html-updates

# DTI-TK installation. Make sure dtitk is present with DTI-TK binary files
# export DTITK_ROOT=/home/virk/devs/WorkProjects/PGI/PGIMRI/dtitk
export DTITK_ROOT=$PWD/dtitk
export PATH=${PATH}:${DTITK_ROOT}/bin:${DTITK_ROOT}/utilities:${DTITK_ROOT}/scripts
which VolumeInfo
TVtool -in ${inputfile} -scale ${factor} -out ${outputfile}

# ITK-SNAP
/home/virk/devs/WorkProjects/PGI/ITKSNAP/lib/snap-3.8.0/ITK-SNAP

## CLI example commands

# Extract subject's zip file
# dtip extract-zip data/DTI/raw_data/S66350\ DEEP-20210530T150739Z-001.zip

# DICOM to NIFTI conversion
# dtip dicom-nifti -m auto -d dicom-nifti-output "S66350 DEEP

# find main DTI files
# dtip locate dicom-nifti-output locate_output

# Make index.txt file
# dtip make-index -d locate_output/index.txt locate_output/DTI_medium_iso_s501.nii.gz

# Make acquisition file
# dtip make-acqparams -d locate_output/acqparams.txt

# Make B0 file
# dtip get-nodif -d locate_output/b0.nii.gz locate_output/DTImediumisos501a1005.nii.gz
