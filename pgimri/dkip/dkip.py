import os
import logging
import shutil
import click
import subprocess
import numpy as np
from fastprogress import progress_bar, master_bar
from datetime import datetime
from pathlib import Path


# Logger settings
logger = logging.getLogger('DKI_Step1_logger')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%d/%B/%Y %I:%M:%S %p')
handler = logging.FileHandler('DKI_Step1.log')
handler.setLevel(logging.DEBUG)
handler.setFormatter(formatter)
logger.addHandler(handler)


def one_subject_to_dicom(datadir: str, save_to:str=None, mb:master_bar=None) -> None:
    f"""This function collects DICOM files from `AVE1` and `B0` folders
    and copies into new folder called `DICOM` at `{datadir}`

    Args:
        > datadir -- Subject folder name. For example, MR076_MR076.
        > save_to -- Save DICOM folder in new location with same directory structure.
        > mb -- master_bar instance for progress_bar.parent.

    Returns: None
    """

    # Set DICOM folder
    if save_to is None:
        savedir = os.path.join(datadir, "DICOM")
    else:
        subject_name = os.path.basename(datadir)
        savedir = os.path.join(save_to, subject_name, "DICOM")
    
    # Create folders if not exist
    os.makedirs(savedir, exist_ok=True)
        
    logger.info(f"data source = {datadir}")
    logger.info(f"Files will be saved at {savedir}")

    # Get DKI data folder path
    dki_datadir = None
    for path in os.listdir(datadir):
        if path.startswith("HEAD_"):
            dki_datadir = os.path.join(datadir, path)
            break

    # Check if DKI data exist
    if dki_datadir is None:
        raise ValueError(f"HEAD_ folder not present in `{datadir}`")

    # get path of all dicom files present in `AVE1` and `B0` folders
    #* This is for AVE1_xxxx folder and B0
    AVE1_folderpath = [
        os.path.join(dki_datadir, path) for path in os.listdir(dki_datadir)
        if path.startswith("DKI_30DIR_AVE1_") and len(path.split("_")) == 4
    ]
    B0_folderpath = [
        os.path.join(dki_datadir, path) for path in os.listdir(dki_datadir)
        if path.startswith("DKI_30DIR_B0_")
    ]
    data_folders = AVE1_folderpath + B0_folderpath

    #* This is for all AVE1 folders and B0
    # data_folders = [
    #     os.path.join(dki_datadir, path) for path in os.listdir(dki_datadir)
    #     if path.startswith("DKI_30DIR_AVE1_") or path.startswith("DKI_30DIR_B0_")
    # ]

    # Copy files from chosen folders to destination folder
    # print(f"Copying {dki_datadir} data to {savedir}")
    for path in progress_bar(data_folders, parent=mb):
        # print(path)
        filepaths = [os.path.join(path, f) for f in os.listdir(path)]
        logger.info(f"Copying `{path}` folder with {len(filepaths)} files to `{savedir}`")
        for fp in filepaths:
            if os.path.exists(fp):
                print(f"[Already exists] @ {fp}. Skipped.")
                logger.info(f"[Already exists] File {fp} already exists. Skipped.")
                continue
            try:
                shutil.copy2(fp, savedir)
            except FileExistsError:
                print(
                    f"[skipped] File {fp} already exists present in {savedir}.")


@click.command()
@click.option("-dd", "--datadir", type=str, help="data folder path to all subjects")
@click.option("-st", "--save_to", type=str, help="save DICOM to new location with same directory structure", required=False)
def to_dicom(datadir:str, save_to:str=None) -> None:
    """Copy `AVE1` and `B0`subdirectories to DICOM folder for each subject in its directory

    Args:
        > datadir -- Data folder path which has all subjects.
        > save_to -- Save DICOM folder in new location with same directory structure.

    Returns: None
    """
    subjects_list = [
        name for name in os.listdir(datadir) if name.startswith("MR")
    ]
    # print(subjects_list)
    n_subjects = len(subjects_list)
    mb = master_bar(range(n_subjects))
    
    for i, subject in enumerate(subjects_list, start=1):
        # Set comment on main bar
        mb.main_bar.comment = f'Copying subject...'
        # Set path
        subject_path = os.path.join(datadir, subject)
        
        one_subject_to_dicom(subject_path, save_to=save_to, mb=mb)
        
        msg = f"[{i}/{n_subjects}] Copied {subject} to DICOM folder."
        mb.write(msg)
        
        logger.info(msg)
        logger.info(f'{"="*10} copied {subject} {"="*10}')

    print("done!")

    logger.info(f"Complete. `to_dicom` processed {n_subjects} subjects.")


# @click.command()
# @click.option("-pf", "--base_params_filepath", type=str, help="main DKEParameters.dat filepath")
# @click.option("-df", "--dicom_folderpath", type=str, help="Subject's DICOM folderpath")
# @click.option("--delete_ima", is_flag=True, type=bool, default=False, show_default=True,  help="Delete IMA files after processing.")
def one_subject_dke(base_params_filepath:str, dicom_folderpath:str, delete_ima:bool=False) -> None:
    """Perform dke <filepath> (DKE-CLI) - IMA to .nii conversion step for one subject

    Args:
        > base_params_filepath -- main DKEParameters.dat filepath which will be used for all subjects.
        > dicom_folderpath -- subject's DICOM folder where all IMA files are copied.
        > del_ima -- If True, delete IMA files from DICOM folder. Default is False.

    Returns: None
    """

    # Open .dat file
    with open(base_params_filepath) as pf:
        params = pf.read().split("\n")
    # Replace the studydir to current subject
    dicom_folderpath = os.path.abspath(dicom_folderpath)
    # print("dicom_folderpath >>", dicom_folderpath)
    for i, line in enumerate(params):
        if line.startswith("studydir = "):
            params[i] = f"studydir = '{dicom_folderpath}';"
    # Set current date and time
    now = datetime.now()
    params[0] = f'% {now.strftime("%a %d/%m/%Y %H:%M:%S")}'
    # Save new params to same DICOM folder as DKEParameters.dat
    subject_params_filepath = os.path.join(dicom_folderpath, "DKEParameters.dat")
    with open(subject_params_filepath, 'w') as f:
        f.write('\n'.join(params))
    
    logger.info(f".dat file created at `{subject_params_filepath}`.")
    logger.info(f"Starting DKE processing...")
    # Run dke command
    # print(f"Starting DKE with {subject_params_filepath}...")
    res = subprocess.run(["C:\\Program Files\\DKE\\dke", subject_params_filepath])
    if res.returncode != 0:
        raise OSError("Return code is not 0 @ DKE subprocess :(")
    # print("DKE Completed.")

    logger.info(f"DKE processing completed for `{dicom_folderpath}` subject.")

    if delete_ima: # delete IMA files after DKE
        ima_files = [
            os.path.join(dicom_folderpath, path) 
            for path in os.listdir(dicom_folderpath)
            if path.endswith("IMA")
        ]

        msg = f"{len(ima_files)} IMA files deleted from `{dicom_folderpath}`."
        logger.info(msg)
        print(msg)
        
        for path in ima_files:
            os.remove(path)


@click.command()
@click.option("-pf", "--base_params_filepath", type=str, help="main DKEParameters.dat filepath.")
@click.option("-dd", "--datadir", type=str, help="main data folder with multiple subjects' data.")
@click.option("--delete_ima", is_flag=True, type=bool, default=False, show_default=True, help="Delete IMA files after processing.")
def multi_subject_dke(base_params_filepath:str, datadir:str, delete_ima:bool=False):
    """Perform dke command (DKE-CLI) - IMA to .nii conversion step for all 
    subjects in the given data directory.

    Args:
        > base_params_filepath -- main DKEParameters.dat filepath which will be 
        used for all subjects.
        > datadir -- main data directory which contains multiple subject's DICOM
        folder with IMA files.
        > del_ima -- If True, delete IMA files from DICOM folder after processing. 
        Default is False.

    Returns: None
    """
    subjects_list = [
        os.path.join(datadir, name, "DICOM")
        for name in os.listdir(datadir)
    ]

    # print("PATHS")
    total_subjects = len(subjects_list)
    for i, path in enumerate(subjects_list, start=1):
        msg = f"[{i}/{total_subjects}] Performing DKE processing on {path}"
        print(msg)
        logger.info(msg)
        one_subject_dke(base_params_filepath, path, delete_ima=delete_ima)
        msg = f"[{i}/{total_subjects}] DKE processing completed."
        print(msg)
        logger.info(msg)

    print("ALL DONE!")
    print(f"Processed {total_subjects} subjects.")
    logger.info("ALL DONE!")
    logger.info(f"Processed {total_subjects} subjects.")



################################ CLI settings #############################
@click.group()
def cli():
    pass

cli.add_command(to_dicom)
# cli.add_command(one_subject_dke)
cli.add_command(multi_subject_dke)

if __name__ == '__main__':
    cli()

# How to use CLI command
# Step 1: Run `to_dicom` to copy DICOM files into new folder
# Step 1 command: python dkip.py to-dicom -dd D:\NIHProjectData\MRIDataSet\ -st .\NIHProjectDataClone\MRIDataSet

# Step 2: Run `multi_subject_dke` for all subjects DKE processing
# Step 2 command: python dkip.py multi-subject-dke -pf DKEParameters.dat -dd .\NIHProjectDataClone\MRIDataSet --delete_ima
