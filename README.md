# Vision-Based-Traffic-Violation

Project Overview

This project utilizes YOLOv8 for car detection. Initially, it detects cars within the frame. Subsequently, a manually configured straight line is introduced into the frame. If the bounding boxes of the cars 
is within this straight line for a certain amount of time, a logic is implemented to capture the images. The captured images are stored in an SQLite database. Additionally, a charts will be generated, providing useful information such as the time and the number of cars that committed violations.

Furthermore, this project will feature a Graphical User Interface (GUI) using PyQt5, ensuring easy access for users.



Project in depth

User Interface

![gui](https://github.com/Layry99/Vision-Based-Traffic-Violation/assets/161226676/94cc6e13-22cd-4997-9f9b-b25ac645f096)


Figure 1 : Interface for main application

The graphical user interface (GUI) has been developed using PyQt5, a cross-platform GUI toolkit that provides Python bindings for Qt v5. PyQt5 enables the development of interactive desktop applications with ease due to its comprehensive tools and simplicity.
On the left side of the home screen, the violation database section is displayed, as shown in Figure 1. Here, users can view a list of images capturing violated vehicles, each with its corresponding ID and timestamp indicating when the violation was captured. Users also have the option to delete images if they believe they are false positives.


Another feature of the violation database is its dynamic nature, meaning the database is refreshed every 10 seconds. If a new detection occurs or users click the delete button, the database will automatically update. This ensures that users always have the latest content in the violation database without needing to restart the program to see updates.


On the right side of the home screen is the video processing section. This area is responsible for analyzing recorded footage based on a specific algorithm. Here’s how it works: when the system detects a car nearing the green line (which we assume marks the white line at a traffic intersection), it initiates a timer. If the vehicle remains within this area for more than 50 seconds, the system identifies it as a violation. In such cases, it captures an image as evidence and stores it in a database.


Additionally, the video processing section displays the current system timestamp, the green line, and bounding boxes around cars for visual reference. It also shows the current vehicle detection counter during video processing at the top right corner. Whenever a violation is detected, red text appears, indicating “Violation detected.”

Violation Dashboard


![image](https://github.com/Layry99/Vision-Based-Traffic-Violation/assets/161226676/0d16092b-4757-46ae-a789-1f90f099ab81)

Figure 2 : Interface for violation dashboard


Based on Figure 2, the webpage will use HTML and CSS for the front-end to define the structure and styling of the web page that users interact with. Python will be used for the back-end, handling server-side logic, including routing, database interactions, and data processing. The back end is implemented using FastAPI, a modern web framework for building APIs with Python.

The webpage will include a chart displaying violations over time, with the x-axis representing the date and the y-axis representing the number of violations. The chart will feature a zoom slider for the x-axis, allowing users to adjust the date range.
Additionally, the webpage will have a card-like feature displaying statistics such as the total number of violations, the maximum number of violations in a day, the minimum number of violations in a day, and the average number of violations per day.


Two pie charts will also be included. The first pie chart will display the top 3 hours with the most violations, and the second will show the days with the highest number of violations.
Users will have the option to select a specific day to view images of violations. If the chosen date does not contain any images, the webpage will display the message: “There is no record found for the selected date. Please select another date.”


Lastly, users will have filtering options to view all images, images from the last month, the last week, the last day, or images from today.


Overall, this webpage can be used to analyze traffic violation patterns, helping to inform decisions regarding road safety measures and enforcement strategies.


For Your Information.
This project is still in development. The software's code will be released as soon as it has been tested many times.
