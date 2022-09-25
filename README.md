# S.W.A.M.P
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
1.	S.W.A.M.P
2.	Training 


Now the training aspect of our program is subdivided to these lesser programs 
1.	mb_joystick.py
2.	mb_receiver.py
3.	remote_control.py	


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
adjusts its steering accordingly.A big advantage of the A.I. solution is that we don’t have to rely on sensors. We only need the camera. Another advantage is that if you exclude the training prosses of the A.I. the program is really simplistic

Program specific analysis:

Mb_joystick.py: contains:

main.py: controls the speed of the vehicle using the analog joystick. It also controls the steering of it, and it can also stop the vehicle from moving 

Mb_reciever.py: contains:

cnf.txt: it’s a text file which incudes values for the different motors of the vehicle, their speed and different color values 

dc.py: it reads the values of the cnf file and can start, stop and set the direction of the robot as well as input new values to the cnf file 

jetson.py: it sends a list of number to jetson and returns the valid list of int numbers

servo.py: after reading the cnf file it can steer the robot. It can also smooth steer the vehicle meaning that in case there are drastically different steer values the transition for one to another will be done in a slower pace to allow the A.I. to correct itself.

main.py: after establishing connection with the microbit on the joystick it awaits the messages it will receive from the joystick and acts according to those.

Remote_control.py contains:

Cnf.txt: it’s a text file which includes values for the pillars as well as the blue and orange line

dc.py: it reads the values of the cnf file and can start, stop, and set the direction of the robot as well as input new values to the cnf file 

jetson.py: it sends a list of number to jetson and returns the valid list of int numbers

servo.py: after reading the cnf file it can steer the robot. It can also smooth steer the vehicle meaning that in case there are drastically different steer values the transition for one to another will be done in a slower pace to allow the A.I. to correct itself.

main.py: after establishing connection with the microbit on the joystick it awaits the messages it will receive from the joystick and acts according to those.

remote_control contains:

cnf.txt: it’s a text file which includes the color values for the pillars as well as the blue and orange line

camera.py: contains the class used to read the camera

microbit.py: establishes a connection between the microbit on the robot and the jetson nano on the robot 

cvtool.py: checks if the camera is open, then it tries to see if the camera is functional. After that it checks if the cnf file is valid, then it reads that file and writes on it. When all of these happen, it opens the camera creates the correct folders and starts taking pictures 

car.py: after calling all the above the training progress can begin.

Now to look at the program that will be used in the competition 
mb_swampTM contains:

cnf.txt: it’s a text file which includes values for the different motors of the vehicle, their speed and different color values

dc.py: it reads the values of the cnf file and can start, stop, and set the direction of the robot as well as input new values to the cnf file 

jetson.py: it sends a list of number to jetson and returns the valid list of int numbers

main.py: it establishes a serial communication between the jetson nano and the microbit on the robot to allow the control of the motors

servo.py: after reading the cnf file it can steer the robot. It can also smooth steer the vehicle meaning that in case there are drastically different steer values the transition for one to another will be done in a slower pace to allow the A.I. to correct itself.

Swamp contains:

resnet18.onnx: the A.I. model. As mentioned earlier we used the A.I. training software from NVIDIA and the overall sample size of all the pictures was 30.000

logfile.log: a tool mainly used for debugging. It was a catalog of what the different sensors see, the battery, the steering values, speed, everything and depending on what level you set it for (debug, warn, error) you can easily detect what wrong with the vehicle or the program.

labels.txt: it’s a simple text file which include all the possible steering values the motors can have. That is used for the A.I. to determine what steering it should have depending on what it currently sees.

car.py: after it imports everything it creates the button objects so that we can set which program it should run (run_1 or run_2). Then it configurates the log file and calls the encoder to regulate the speed of the robot. Finally the real program can start and using the A.I. model it can finish the task that has been given
