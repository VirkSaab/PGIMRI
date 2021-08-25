# Folders settings
PROCESSED_DATA_FOLDERNAME = "processed_data"
PROCESSED_DTI_FILENAME = "dti"

# DTI data file names to filter the relevant files
DTI_FILENAMES_LIST = ["dti_medium_iso", "dtimediumiso"]
# If there are some files with the same name as `dti_medium_iso` such as `faregdti_medium_iso` then enter those names
EXCLUDE_LIST = ["reg", "fareg"]
# extensions of metadata files
META_EXTENSIONS = ['.bval', '.bvec', '.json']

# Scan Parameters
N_DTI_VOLUMES = 16

# Acquisition parameters
AP_PE = [0, -1, 0]
PA_PE = None#[0,  1, 0]
# if you can't find the "total readout time" for your
# own data: you can almost always use 0.05.
# as mentioned in the below link, `Running topup` section:
# https://fsl.fmrib.ox.ac.uk/fslcourse/lectures/practicals/fdt1/index.html
READOUT_TIME =  0.05

# Go to this link to read more about the below DTITK_UODMF variable:
# http://dti-tk.sourceforge.net/pmwiki/pmwiki.php?n=Documentation.Diffusivity
DTITK_UODMF = 1000 # UNIT OF DIFFUSIVITY MULTIPICATION FACTOR

# To perform bootstrap without an existing template, manually select a subset
# of subjects (5 or so) with good alignment among them. Below is the list of 
# folder names of good aligned subjects. Manually visualize the DTI volumes
# and add there names here
BEST_POPULATION_SUBSET = ['1_1', '1_2', '6_1', '7_2', '9_2', '11_1']

# Number of iterations for `dti_rigid_population` and `dti_affine_population` commands for image registration.
NUM_ALIGN_ITERS = 5


# Logging settings, Either CRITICAL, ERROR, WARNING, INFO or DEBUG.
LOG_FILENAME = "ITC_DTI_processing_logs.log" # Set to `None` if you do not want to create a log file.
LOG_LEVEL = "DEBUG"
FILE_LOG_LEVEL = "DEBUG"
LOGGING_FILE_FORMAT = '%(asctime)s - %(name)s - [%(levelname)s] - %(message)s'
LOGGING_DATEFMT = '%d/%B/%Y %I:%M:%S %p'
