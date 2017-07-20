# PPPLCalibrationFramework
A tool to scan through multiple hardware axis and take measurements for the Princeton Plasma Physics Lab

This was developed during an internship for the [Princeton Plasma Physics Laboratory](http://www.pppl.gov/) (PPPL), sponsored by the DoE and run by Princeton University.

If you have ever needed to painstackenly scan through multiple dimensions are record measurements at each point, then this is for you!

Quickly scan through multiple points along many different axis (X, Y, power, frequency, etc) and measure the value(s) of a sensor at each one.

**Features:**
 - Quickly create and configure axis to scan through
 - Jog axis manually
 - Specify a list of points to scan
 - Import a CSV of pre generated points
 - Export measured data to CSV
 
 **Supported Axis:**
 - [Thorlabs LTS150](https://www.thorlabs.com/newgrouppage9.cfm?objectgroup_id=3961&pn=LTS150#8110) Linear Stage
 - [Thorlabs BSC201](https://www.thorlabs.com/newgrouppage9.cfm?objectgroup_id=1704&pn=BSC201) Stepper motor controller
 - Laser Power and Frequency using
   - [GW Instek AFG-3021](http://www.gwinstek.com/en-global/products/Signal_Sources/Arbitrary_Function_Generators/AFG-303x) Arbitrary Function Generator
   - [GW Instek GPD-4303S](http://www.gwinstek.com/en-global/products/DC_Power_Supply/Programmable_Multiple_Channel_DC_Power_Supplies/GPD-Series) Power Supply

**Supported Sensors**
 - [Thorlabs PDA36A](https://www.thorlabs.com/newgrouppage9.cfm?objectgroup_id=3257&pn=PDA36A#10781) Photodetector
 - [Thorlabs DCC1545M](https://www.thorlabs.com/newgrouppage9.cfm?objectgroup_id=4024) Camera
 
