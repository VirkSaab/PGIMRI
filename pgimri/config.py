# Folders settings
PROCESSED_DATA_FOLDERNAME = "processed_data"

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
