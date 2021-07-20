import dicom2nifti



if __name__ == '__main__':
    dicom2nifti.convert_directory("raw_data/S63080 HARSH ITS", "test_out", compression=True, reorient=True)
