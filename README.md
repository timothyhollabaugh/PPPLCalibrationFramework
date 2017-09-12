# PPPLCalibrationFramework
A tool to scan through multiple hardware axis and take measurements for the Princeton Plasma Physics Lab

This was developed during an internship for the [Princeton Plasma Physics Laboratory](http://www.pppl.gov/) (PPPL), sponsored by the DoE and run by Princeton University.

If you have ever needed to painstackenly scan through multiple dimensions are record measurements at each point, then this is for you!

Quickly scan through multiple points along many different axis (X, Y, power, frequency, etc) and measure the value(s) of a sensor at each one.

**Note:** This requires a custom fork of the Pyforms library: [https://github.com/chickenchuck040/pyforms](https://github.com/chickenchuck040/pyforms)

**Features:**
 - Quickly create and configure axis to scan through
 - Jog axis manually
 - Specify a list of points to scan
 - Import a CSV of pre generated points
 - Export measured data to CSV
 
 **Supported Axis:**
 - [Thorlabs LTS150](https://www.thorlabs.com/newgrouppage9.cfm?objectgroup_id=3961&pn=LTS150#8110) Linear Stage
 - [Thorlabs BSC201](https://www.thorlabs.com/newgrouppage9.cfm?objectgroup_id=1704&pn=BSC201) Stepper motor controller
 - [BlueLyte LC Laser](http://www.global-lasertech.co.uk/wp-content/uploads/2014/04/BlueLyte_LC_Userguide_EN.pdf) Power and Frequency using
   - [GW Instek AFG-3021](http://www.gwinstek.com/en-global/products/Signal_Sources/Arbitrary_Function_Generators/AFG-303x) Arbitrary Function Generator
   - [GW Instek GPD-4303S](http://www.gwinstek.com/en-global/products/DC_Power_Supply/Programmable_Multiple_Channel_DC_Power_Supplies/GPD-Series) Power Supply

**Supported Sensors**
 - [Thorlabs PDA36A](https://www.thorlabs.com/newgrouppage9.cfm?objectgroup_id=3257&pn=PDA36A#10781) Photodetector
 - [Thorlabs DCC1545M](https://www.thorlabs.com/newgrouppage9.cfm?objectgroup_id=4024) Camera
 - [PCI DV C-Link](https://edt.com/product/pci-dv-c-link/) Cameralink frame grabber 

# Dependencies
Many python dependancies are required for this program to run
## Thorlabs APT
 In order to control the Thorlabs APT motion stages, the thorlabs APT library is used.
 This can be downloaded and installed from https://www.thorlabs.com/software_pages/ViewSoftwarePage.cfm?Code=Motion_Control
 
 At first, I was using the 32 bit for software for 64 bit windows, along with 32 bit python, to get it to work with python.
 I may have gotten it to work with everything 64 bit.
 
 To interface to python, I used https://github.com/qpit/thorlabs_apt. You will need to copy APT.dll from the "APT installation path\APT Server" directory to the `thorlabs_apt/thorlabs_apt` directory with `__init__.py`. Then, you will need to edit the `setup.py` file in thorlabs_apt to copy `APT.dll` to the installation directory when it installs. Including the line `package_data={'': ['APT.dll']}` in the `setup` function call in `setup.py` should work (See https://stackoverflow.com/questions/1612733/including-non-python-files-with-setup-py). Then run `python setup.py install` to install it.
 
## Labjack
 In order to talk to the Labjack T7 Pro used to read the photosensor, the labjack Python for LJM library was used: https://labjack.com/support/software/examples/ljm/python. Follow the directions there to download and install both Python for LJM and the LJM library.
 
## Pyforms
 To create the GUI, a custom fork of the [pyforms](https://github.com/UmSenhorQualquer/pyforms) library was used. The fork can be found at https://github.com/chickenchuck040/pyforms. It includes fixes that have not yet been merged into pyforms yet.
 To install, run `python setup.py install`.
 Dependancies for Pyforms can be found at http://pyforms.readthedocs.io/en/v2.0/#installation. Of the optional dependancies listed, PyOpengl, Numpy, and Python OpenCV are needed.

## Cameralink Framegrabber and FLIR Tau 2 camera
 In order to talk to the [PCI DV C-Link](https://edt.com/product/pci-dv-c-link/) framegrabber, you must download and install the PDV software and drivers from https://edt.com/file-category/pdv/.
 The configuration for the Tau2 camera can be found in the `flir` directory in this repository. These must be copied to `C:\EDT\pdv\camera_config`. There is one file for the 8 bit mode on the camera, and one for the 14 bit mode. This calibration program uses the 14 bit mode. The corresponding mode must be selected in the FLIR camera controller GUI before use. The FLIR camera controller GUI can be downloaded from http://www.flir.com/cores/display/?id=51880.
 Also, the correct configuration file must be selected by running the `pdvshow` application. This will let you view the image from the camera and ensure that it is working properly.
 
 
