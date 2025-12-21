# LMGC90_GUI — Graphical User Interface for LMGC90

![LMGC90_GUI Screenshot](docs/inter_LMGC90_GUI6.jpg)

**LMGC90_GUI** is a modern, user-friendly graphical interface built with **PyQt6** for the pre-processor module (`pre`) of the open-source Discrete Element Method (DEM) code **[LMGC90](https://git-xen.lmgc.univ-montp2.fr/lmgc90/lmgc90_user/-/wikis/home)** and **[LMGC90 documentation](https://lmgc90.pages-git-xen.lmgc.univ-montp2.fr/lmgc90_dev/index.html)**

It allows you to visually create, edit, and manage complex 2D (and partially 3D) mechanical models without writing Python code manually — while still offering full flexibility for advanced users.

All versions are intended for research and prototyping. A full rewrite is planned in the future.

## Features

- **Materials**: RIGID, ELAS, ELAS_DILA, VISCO_ELAS, ELAS_PLAS, THERMO_ELAS, PORO_ELAS
- **Models**:
  - 2D: Rxx2D, T3xxx, Q4xxx, T6xxx, Q8xxx, Q9xxx, BARxx
  - 3D: Rxx3D, H8xxx, SHB8x, H20xx, SHB6x, TE10x, DKTxx
- **Rigid bodies** (avatars): disks, polygons (regular or full), ovoids, joncs, clusters, walls (rough/fine/smooth/granular), spheres (3D not implemented), and fully customizable **empty avatars** with multiple contactors
- **Contact laws**: IQS_CLB, IQS_CLB_g0, COUPLED_DOF
- **Visibility tables** for detection control
- **Boundary conditions** (imposeDrivenDof, translate, rotate, etc.) on individual bodies or **named groups**
- **Parametric generation**:
  - Loops (circle, grid, line, spiral, manual)
  - Granulometry with random size distribution and deposition in Box2D or Disk2D
  - Option to store generated particles in a **named group**
- **Granulmetry** : 
  - *granulo_Random* distrinution 
  - deposit in (Box2D, Disk2D, Drum2D and Couette2D) 
  - Option to store granolo in **named group**
- **Post-processing commands** (SOLVER INFORMATIONS, TORQUE EVOLUTION, BODY TRACKING, etc.) with optional rigid set selection
- **Dynamic variables**: define custom variables (e.g., `thickness=0.02`, `scale=1.5`) usable in parameter fields
- **Direct generation** of `.Datbox` file (ready for LMGC90 solver)
- **Python script generation** for full reproducibility
- Project save/load in `.lmgc90` JSON format

## Requirements
- Python 3.8+
- PyQt6
- pylmgc90 (installed with LMGC90)


## Installation

```bash
git clone https://github.com/bzerourou/LMGC90_GUI.git
cd LMGC90_GUI
python main.py
```

## Quick Start & Examples
Two example projects are included to help you get started.
1. ### Pendulum (pendulum.lmgc90)
A classic pendulum mechanism using COUPLED_DOF joints.
**How to load and run**:

1. Launch *LMGC90_GUI* → *File* → *Open* → select *pendulum.lmgc90*
2. Go to Tools → *Generate Datbox*
3. The file *DATBOX* is created in the project folder

2. ### Slider-Crank Mechanism (slider_crank.lmgc90)
A complete slider-crank (bielle-manivelle) with three rigid bodies connected by revolute and prismatic joints.
How to load:
1. *Fil*e → *Open* → select *slider_crank.lmgc90*
2. Generate *Datbox* (*Generate Datbox*)

## Changelog (Highlights)

- **0.2.7**: Dynamic variables dialog (Tools → Define dynamic variables)
- **0.2.6**: Direct .Datbox generation + post-processing commands + granulometry groups
- **0.2.5**: Units preferences + basic post-processing
- **0.2.4**: Granulometry with deposition (Box2D/Disk2D)
- **0.2.3**: COUPLED_DOF and IQS_CLB_g0 laws
- **0.2.2**: Custom contactors in empty avatar tab
- **0.2.0**: Stable version with empty avatars and advanced contactors
- **0.1.9**: Parametric loops + named groups

## License
Open source — free to use, modify, and distribute.

## Author
Zerourou Bachir
Email: bachir.zerourou@yahoo.fr
© 2025