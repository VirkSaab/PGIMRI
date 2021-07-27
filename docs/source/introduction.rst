Introduction
================

What is PGI-MRI?
-----------------

PGI-MRI is a CLI tool to process a few MRI modalities. I created this tool while I was working at `PGIMER Chandigarh <https://pgimer.edu.in>`_ as an MR Image Processor.
This is a Python wrapper based on `dcm2nii <https://people.cas.sc.edu/rorden/mricron/dcm2nii.html>`_ and `FSL <https://fsl.fmrib.ox.ac.uk/fsl/fslwiki>`_. Currently, this package processes two modalities:

1. Diffusion Kurtosis Imaging (DKI)

2. Diffusion Tensor Imaging (DTI)

Future versions will include:

3. Magnetic Resonance Spectroscopic Imaging (MRSI)

4. Functional MRI (fMRI)

.. important::
    This is not a complete solution and might not work out of the box but you can use it as a reference if you are new to DKI, DTI, MRSI, and fMRI image processing. I created this tool to automate some operations which are redundant for multiple subjects.


Check out the :doc:`installation` tab to install this package.