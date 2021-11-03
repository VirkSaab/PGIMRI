# PGIMRI

**PGIMRI** is a wrapper package for Diffusion Kurtosis Imaging (DKI) and Diffusion Tensor Imaging (DTI) for a couple of projects I did at PGIMER, Chandigarh, India. This code is based on data from Philips Ingenia 3T MRI Scanner. This code might not work out of the box but, if you are a begineer like me, you can use it as a reference.


## DTI ITC project
The objective of this project is to compare two groups of scans taken before and after the diagnosis.

### DTI Image Processing and registration
DTI processing steps are heavily based on FSL. I used [this tutorial](https://fsl.fmrib.ox.ac.uk/fslcourse/lectures/practicals/fdt1/index.html#diffdata) for TOPUP, EDDY, and DTIFIT steps. I used MRtrix3 for denoising. Denoising is applied just before the TOPUP step. After DTIFIT, image registration is performed using DTI-TK toolkit. For image registration, I followed [these tutorial](http://dti-tk.sourceforge.net/pmwiki/pmwiki.php?n=Documentation.HomePage).

I implemented all these steps in one command:

```bash
dtip process -o <output folder> <subject folder>
```
This command saves data at every major step. Below is the list of folders it creates
* `0_extracted` - if the input is a .zip file. Otherwise, this folder would not be created.
* `1_nifti` - DICOM to NIfTI converted data
* `2_interm` - this folder contains preprocessed data from the *denoising*, *topup*, and *eddy correction* steps.
* `3_processed` - outputs of `dtifit` tensor fitting step.
* `4_registred` - outputs of DTI-TK image registration.


This command performs the following steps in the given order. Each step has its own command as well. Type `dtip` in terminal and see the `Commands` section for all the commands:

**Note**: Type `--help` to know more about commands

0. If the given input path to the `dtip process` is a .zip file then it will extract the contents in the `0_extracted` folder. The command is 
    ```bash
    dtip extract-zip -o data/processed data/raw/subject.zip
    ```
1. Convert the DICOM data to NIfTI format. This step uses `dcm2nii` and `dcm2niix` sub-package command of MRICron tool. You can select from 3 options if you want specific tool. Otherwise, the default is `auto`. Type `dtip dicom-nifti --help` for more information. The command for conversion is
    ```bash
    dtip dicom-nifti -o data/processed/1_nifti data/raw/subject_folder
    ```
    The output of this command will be saved in `1_nifti` folder.
2. Locate the relevant DTI files from the NIfTI data. For this project the files I want have names like `DTImediumiso` or `dti_medium_iso`. This command will look for the filenames given in `DTI_FILENAMES_LIST` variable (check config.py file for this variable). Along with that, `META_EXTENSIONS` variable contains the relevant file extensions. This will copy the found files to `2_interm` folder. The default settings is to find a DTI.nii.gz data file, bval and bvec files, and a json file with metadata in it. The command is 
    ```bash
    dtip locate <input folder> <output folder>
    ```
3. The selected DTI file will be denoised using `dwidenoise` command from MRtrix3 tool. There is no wrapper for this command because you can directly use it by typing `dwidenoise` in the terminal.
4. TOPUP command requires 2 additional files - a b0 volume file and, an acquisition parameters file. The commands to create them are:
    ```bash
    dtip make-acqparams
    dtip make-b0
    ```
    Type `--help` with the above commands for more details.

    To perform TOPUP the command I use is FSL's `topup` command. Type `topup` in terminal to know more about it. The outputs of TOPUP will be saved in `2_interm` folder.
5. Next, is eddy current corrections. To perform eddy correction we need:

    * average b0 file which can be generated using the following command:
        ```bash
        fslmaths <input path> -Tmean <output path>
        ```
    * an index.txt file containing 1 for each row for each 3D volume in the DTI file. The command for this is
        ```bash
        dtip make-index
        ```
    
    Here, if the skull stripping is enabled (by default it is enabled), BET is used to remove the non-brain part from the DTI volume and create a brain mask. Then, eddy coorections are performed using FSL's eddy command. Type `eddy` in terminal for more details.
6. After that, DTIFIT is performed for tensor fitting. This is performed using FSL's `dtifit` command. Type `dtifit` in terminal for more details.
7. Next, is image registration using DTI-TK tool. We need to convert the NIfTI format to DTI-TK required. It provides the command to that which is
    ```bash
    fsl_to_dtitk
    ```
    

# Note for ITC project
* Two ways to register images based on population registering for this particular task, however, image processing is same.
    1. Use one `initial_mean` template image for population registration for both before and after scans.
    2. Use group wise population template. Where before and after scans has their own `initial_mean` template.

