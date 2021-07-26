#!/bin/bash
# This file contains the CLI commands to preprocess and clean `ITS cases` data
# Source - https://fsl.fmrib.ox.ac.uk/fslcourse/lectures/practicals/fdt1/index.html#pipeline
##########################

# Create `processed_data` folder structure
ROOT_DIR="."
processed_datadir="$ROOT_DIR/processed_data"
nifti_dir="$processed_datadir/1_nifti"
topup_dir="$processed_datadir/2_topup"
eddy_dir="$processed_datadir/3_eddy"
dtifit_dir="$processed_datadir/4_dtifit"

mkdir $processed_datadir
mkdir $nifti_dir
mkdir $topup_dir
mkdir $eddy_dir
mkdir $dtifit_dir

# Subject 1
subject_id="S63080"
# Step 1: RAW Philips scanner images to infti. (FOR EACH SUBJECT)
step_1(){
  subject_savedir="$nifti_dir/$subject_id"
  mkdir $subject_savedir
  echo "Saving @ $subject_savedir"
  dcm2niix -o $subject_savedir -z y -p y "raw_data/S63080 HARSH ITS"
  echo ">>>> [Step 1] results saved @ $subject_savedir"
}


# Step 2: TOPUP - Correcting for Susceptibility-induced Distortions
step_2(){
  savedir="processed_data/2_topup/$subject_id"
  mkdir -p $savedir
  save_filepath="$savedir/nodif.nii.gz"
  fslroi "$1" $save_filepath 0 1
  echo ">>>> [Step 2] results saved @ $save_filepath"
  echo ">>>> [??] incomplete! Where is nodif_PA?"
}

# Step 3: Eddy currents correction
step_3(){
  bet2 processed_data/2_topup/S63080/nodif.nii.gz processed_data/3_eddy/dti_b0 -m -f 0.2
}




# step_2 processed_data/1_nifti/S63080/S63080\ HARSH\ ITS_DTI_medium_iso_20201201124757_801.nii.gz
