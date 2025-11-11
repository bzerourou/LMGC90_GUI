Graphical User Interface for LMGC90 with PyQt6.


This application is a PyQt6 graphical user interface intended for those who want to develop numerical models with LMGC90 DEM code.

version 0.1.0 is only for feasibility study, it will be completely rewritten in the future.

For use, you need to download PyQt6 and, of course, install LMGC90 on your machine.



In this first version,it is completely independant of the pylmgc90 library routines, you can create materials, models, **rigidDisk**  avatars,  and Coulomb friction contact laws with  __'IQS_CLB'__ type. 
You can also apply boundary conditions for this avatars with **translate**, **rotate** and **imposeDrivenDof** functions.

the interface can save and open project with json formated file, and can generate and execute model script.

[Intro LMGC90_GUI](https://www.youtube.com/watch?v=Rn-ewPCuRuw)

List of version : 
-  0.1.0  : first version with `rigidDisk` avatar; 
-  0.1.1  : add `rigidJonc` avatar;
-  0.1.2 : add DOF function `imposeDrivenValue`;
-  0.1.3 : add `rigidPolygon` avatar and fix `rigidPolygon` generation type in QComboBox for `regular` qnd `full` values, numpy and math function can be used in QEditLine ;
-  0.1.4 : add rigidOvoidPolygon and fix some bugs;
-  0.1.5 : add `rigidDiscretDisk`, `roughWall`, `fineWall`, `smoothWall`, and `GranuloRoughWall` avatars;
 