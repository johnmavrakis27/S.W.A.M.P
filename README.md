# fast_and_vicious.
This is a project that will attend the WRO 2022 future engineers competition  
# Content
T-photos contains 2 photos of the team (an official one and one funny photo with all team members)

v-photos contains 6 photos of the vehicle (from every side, from top and bottom)

video contains the video.md file with the link to a video where driving demonstration exists

schemes contains one or several schematic diagrams in form of JPEG, PNG or PDF of the electromechanical components illustrating all the elements (electronic components and motors) used in the vehicle and how they connect to each other.

src contains code of control software for all components which were programmed to participate in the competition

models is for the files for models used by 3D printers, laser cutting machines and CNC machines to produce the vehicle elements. If there is nothing to add to this location, the directory can be removed.

training_photos_for_ai: includes an older version of the programm used to train the A.I. 

# Introduction
WRO Future Engineers, S.W.A.P Introduction 
Our program consists of 2 main parts:
1.	Swamp
2.	Training 


Now the training aspect of our program is subdivided to these lesser programs 
1.	mb_joystick
2.	mb_receiver
3.	remote_control	


Now we will go over what these parts, do how they interact with the robot and what is the process to build/compile/upload the code to the vehicle’s controllers.
Firstly, we will look at how we trained our A.I. The mb_joystick is the program that runs the microbit joystick to control the robot in training mode. More
specifically, it uses radio signals to communicate with the microbit in our robot in cohesion with the mb_receiver program (more on that later) and using a joystick,
we are able to steer our robot in the correct way. The mb_receiver is the program that runs the microbit receiver, it listens to the data sent by the joystick and
applies them to the drive motors. Finally, the remote_control program run on jetson nano, collects all the data sent by the joystick and the receiver and using the
camera it takes pictures. More notably using the data that it has collected it moves the vehicle according to them taking 300 photos per minute, saving them in the
correct file based on the steering values the robot had when it took the picture. Using these three programs we run different scenarios on the track to get a good
sample size. After that was done, we used the AI procedure by NVIDIA ([click here to see it](https://github.com/dusty-nv/jetson-inference/blob/master/docs/pytorch-collect.md)) to train our model.

Now that we covered how we built our data base let’s see how the main program runs.
Its main utility is to use the classification training model (onnx) to drive the car. It achieves that by comparing the frame the robot is seeing to its model and
adjusts its steering accordingly. 
