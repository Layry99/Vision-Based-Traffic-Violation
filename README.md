# Vision-Based-Traffic-Violation

Project Overview

This project utilizes YOLOv8 for car detection. Initially, it detects cars within the frame. Subsequently, a manually configured straight line is introduced into the frame. If the bounding boxes of the cars 
is withhin this straight line for a certain amount of time, a logic is implemented to capture the images. The captured images are stored in an SQLite database. Additionally, a charts will be generated, providing useful information such as the time and the number of cars that committed violations.

Furthermore, this project will feature a Graphical User Interface (GUI) using PyQt5, ensuring easy access for users.

Interface

![image](https://github.com/Layry99/Vision-Based-Traffic-Violation/assets/161226676/ca8cd050-12b6-4d84-a7b1-5187440f7571)

Figure 1 : Interface for the home screen

On the left side of the home screen, the violation database section is displayed, as shown in Figure 1. Here, users can view a list of images capturing violated cars, each with its corresponding ID and timestamp indicating when the violation was captured. Users also have the option to delete images if they believe they are false positives.


Another feature of the violation database is its dynamic nature, meaning the database is refreshed every 15 seconds. If a new detection occurs or users click the delete button, the database will automatically update. This ensures that users always have the latest content of the violation database without needing to restart the program to see updates.


On the right side of the home screen, this is the video processing section. This area is responsible for analysing recorded footage based on a specific algorithm. Here's how it works: when the system detects a car nearing the green line (which we assume marks the white line at a traffic intersection), it initiates a timer. If the car remains within this area for more than 3 seconds, the system identifies it as a violation. In such cases, it captures an image as evidence and stores it in a database.


Additionally, the video processing section displays the current system timestamp, the green line, and bounding boxes around cars for visual reference. Whenever a violation is detected, a red text appears, indicating 'Violation detected'.


![image](https://github.com/Layry99/Vision-Based-Traffic-Violation/assets/161226676/beea4dd1-0b47-4f1f-9719-40821c31feff)


Figure 2 : Larger size of image for the violating car

If the image of the violating car appears too small or blurry on the home screen in the violation database section, users can click on the image. This action opens a new window displaying the original captured image retrieved from the SQLite database. This provides users with a clearer and smoother picture.


![image](https://github.com/Layry99/Vision-Based-Traffic-Violation/assets/161226676/08a15fdb-345f-490c-9944-2c59e25f49e9)


Figure 3 : Analysis and reporting 

When the "Analysis and Reporting" button on the main home screen is clicked, it will display Figure 3, which shows statistics of violations within a day. The data is retrieved from the violation database. The x-axis represents the date, and the y-axis represents the number of violations detected. Over time, the system can be used to analyze traffic violation patterns and generate reports to inform decisions on road safety measures and enforcement strategies.


For Your Information.
This project is still in development. The software's code will be released as soon as it has been tested many times.
