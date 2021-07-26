export PYTHONPATH=$PYTHONPATH:pgimri

# Check if the script is working
python pgimri/dtip/dtip.py --help

# Create a requirements files
pip list --format=freeze > requirements.txt

# install pgi package with editable mode
pip install --editable .


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