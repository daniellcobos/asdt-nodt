# 1. Introduction
This document provides an architectural overview of the Easynet (temporal name) application, its infrastructure and the stack of software that makes the application work

## 1.1 Purpose
The purpose of Easynet is to provide Abbvie sales representatives a way to administer and check their bonifications over sales, known as Freegoods. The system provides different levels of users an overview of those bonifications, who receives them and the quantities required.
##1.2 Scope
This system only has one objective, the administration of freegoods, hence there application is small on infrastructure, database and code. This applicaction is made for few simultaneous users, in a 1-5 range. The application only handles general sales data and does not have any kind of medical records.
##1.3 Definitions:
- Flask: A framework done on Python to develop web micro applications
- Freegood: A promotional bonification granted to Allergan/Abbvie clients over a preestablished sales goal.
- Service: On this document, Service refers to the middleware that connects the Flask source code to the Nginx server, using uwsgi.
- Uwsgi: A python server that connects Python web applications to a production server like Nginx or Apache
# 2. General Description
# 2.1 System Overview
This a Web Application made on Flask, which implies that the source code is made on Python, this is a Server-Side rendered application so there is no frontend framework for the web pages, in its place Vanilla Javascript, Jquery and addtional required libraries are called on the HTML templates using CDNs to provide front-end functionalities.
The system uses a PostgreSQL database to store data, is a very small database so its on the same virtual machine than the Flask application. The Flask application connects and send SQL queries to said database using the Psycopg2 Python library. 
The web page also requires importation and exportation of data as spreadsheets, so addtional libraries are used for that purpose. 
Finally there are different levels of users, which restrict the different functionalities that said user is able to access to, there are administrators, consultants, department heads and customer service users.
# 2.2 Tools Used
1. Flask, a python based web development framework is used to handle all the backend logic and the basic rendering of the webpages
2. Postgresql is used the as the database, stores all the data
3. Nginx is used the server that handles the network logic and displays the web application
4. Uwsgi is used as a middleware to create a systemctl service that connects the web application with the nginx server
5. Flask-Login handles the authentication logic
6. Pandas and Openpyxl are used to read and export spreadsheets
7. Jquery and Datatables are used to grant front-end functionalities to the web pages required to render different tables.
8. Bootstrap is used to add aesthetic elements to the web pages
9. The server platform is Linux
# 2.3 General Constraints
The web application must be user friendly, the users are not required to have technical knowledge about how the application works, the administrators handle the accounts, meaning that the user accounts are given to the users by the administrators. The functionalities of the application available to the user are dependent of its user level.
# 2.4 Special Design Aspects
When the application was initially designed its was thought of as a internet application, but now its thought as system that will only be accessible inside an intranet network, which may restrict functionalities
# 3.Design Details
## 3.1. Main Design Features
 The main design features include five major parts: the architecture, the user interface design, external interface, the database, process relation, and automation.  
## 3.1 Techology Architecture
 ![alt text](add.png "Architecture Diagram")
### 3.1.1 Web Application Architecture
The Web Application itself follows the Flask Architecture principles, it establishes what routes (urls) execute determinated business logic and which template will be rendered, in addition to that once a user is logged it will determine what functionalities and pages said user can access. If a user is not logged any functional route will automatically redirect to the login page.
### 3.1.2 Presentation Layer
As previously said, different users will get different functionalities, in general terms:
- Administrators: Can create and edit user, see all the freegood information of his country, edit it and alter the parameters upon those freegoods are granted. 
- Consultants: Can create deals and add parameters to calculate freegoods on their charge. 
- Department Heads: Can see the all the freegood deals and authorize/approve them
### 3.1.3 Data Access Layer
Only the Synapsis system administrators have direct access to the postgres database, the different user levels determine what changes and sql queries a user has access to in the web application. 
### 3.2. Standards
 - Database – Relational Database
 - Inputs – entered through text field and stored in database. There are also functionalities that accept an excel spreadsheet as input
 - Security – username and password are required for access to the system. The password is salted and hashed, so no plaintext goes into the database or the connection. There are minumun requirements for the password too so its not easy to guess
 ### 3.3 Database Design
  ![alt text](try2.png "Database Diagram")
 ### 3.4 Files
 The application uses spreadsheets since is the most friendly option to load data and to show outputs, there are also logs made to track the application status 