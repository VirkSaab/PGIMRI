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
This command saves data for every major step. Below is the list of folders it creates
* `0_extracted` - if the input is a .zip file. Otherwise, this folder would not be created.
* `1_nifti` - DICOM to NIfTI converted data
* `2_interm` - this folder contains preprocessed data from the *denoising*, *topup*, and *eddy correction* steps.
* `3_processed` - outputs of `dtifit` tensor fitting step.
* `4_registred` - outputs of DTI-TK image registration.


This command performs the following steps in the given order. Each step has its own command as well. Type `dtip` in terminal and see the `Commands` section for all the commands:

**Note**: Type `--help` to know more about commands

0. Either pass subject folder or .zip file which contains DICOM images. This step will convert the DICOM data to NIfTI format. The command for this step is
    ```bash
    dtip dicom-nifti -o data/processed/1_nifti data/raw/subject_folder
    ```
    Use the following for more details
    ```bash
    dtip dicom-nifti --help
    ```
    To extract .zip file use
    ```bash
    dtip extract-zip -o data/processed data/raw/subject.zip
    ```
1. 
2. 



### DTI Image Registration
* Two ways to register images based on population registering for this particular task, however, image processing is same.
    1. Use one `initial_mean` template image for population registration for both before and after scans.
    2. Use group wise population template. Where before and after scans has their own `initial_mean` template.


