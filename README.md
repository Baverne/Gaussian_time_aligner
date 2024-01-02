# The code is separated in two parts.

	1. Cameras_images_to_frames_gaussian_splatting.ipynb

It processes the frames from the different cameras in order to obtain the required gaussian splatting models.

	2. Tiny Gaussian Splatting Viewer 

It loads the gaussian platting models one after the order in order to vizualise de motion

# Cameras_images_to_frames_gaussian_splatting.ipynb :

# Requirements:

-Python
-Inria's Gaussian-splatting implementation installed (https://github.com/graphdeco-inria/gaussian-splatting)
-Colmap (https://colmap.github.io/install.html)
-The source data files (https://we.tl/t-sPWec4L4ns)

The source data files contains :
-A raw_data folder, which are waiting to be processed by Cameras_images_to_frames_gaussian_splatting.ipynb
-A traited_data folder, which is the expected result of the treatment.

# Usage

To run the code, provide the path to the gaussian splatting folder and to the raw_data folder in the first cell. 
Run all the cells.
The last cell run 10 gaussian training which can take roughly an hour to run.


# Tiny Gaussian Splatting Viewer

This viewer is based on this repository to which we added a few modifications.

# Usage
Install the dependencies:
```
pip install -r requirements.txt
```

Launch the viewer:
```
python main.py
```

# Modifications

To use the viewer as a video viewer, you simply need to place all the splats in the splats folder with naming such as they will be sorted by frame number when loaded.

We simply modified the functions for loading the gaussians with : load_ith_gaussian, as well as in the main animation loop we added a fixed framerate and changed the current gaussian every 20 frame to give time for the next one to load.

We also had to modify and remove a few openGL functions to allow for a smooth transition between frames.


