# Folders settings
PROCESSED_DATA_FOLDERNAME = "processed_data"

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

# Logging settings, Either CRITICAL, ERROR, WARNING, INFO or DEBUG.
LOG_FILENAME = "ITC_DTI_processing_logs.log" # Set to `None` if you do not want to create a log file.
LOG_LEVEL = "DEBUG"
FILE_LOG_LEVEL = "DEBUG"
LOGGING_FILE_FORMAT = '%(asctime)s - %(name)s - [%(levelname)s] - %(message)s'
LOGGING_DATEFMT = '%d/%B/%Y %I:%M:%S %p'
