# SP 24 DSCI551 Final Project - Team #40

This repository contains all the necessary code and database setup required for the DSCI551 final project hosted on an EC2 instance.

## Project Overview

All code and databases are designed to run on an Amazon EC2 instance with MongoDB installed. Code can be transferred to the EC2 instance using the `scp` command.

For a detailed walkthrough on setting up and running the project, please refer to this video tutorial:
[Project Setup Video](https://youtu.be/L4tLTKVzk_A)

## Setup Instructions

### Step 1: Data Preparation & Database Input

1. Navigate to the `apartment_data` folder.
2. Run the following Python scripts in order to process and hash the raw data into MongoDB on your EC2 instance:
   - `toJSON.py` - Converts raw data to JSON format.
   - `add_geocode.py` - Adds geocode information to the data.
   - `toMongoDB.py` - Uploads the processed data to MongoDB.

### Step 2: Launching the Backend

1. Change directory to the `query` folder and activate the project
   ```bash
   cd query
   python3 backEndMG.py

Here is the text translated into a format suitable for a README file:

---
### Step 3: Accessing the Application and Database

- **Accessing the Web Page:**
  Users can access the web page via the EC2 instance's Public IPv4 address at port 5000. Simply enter `http://<Public-IPv4-address>:5000` in your web browser.

- **Accessing the Database:**
  Managers can access the corresponding databases directly on the EC2 instance. Use the MongoDB Shell (mongosh) by executing `mongosh`, and then connect to the database with the command `use finalProject_db`.
---

![flow diagram](flowmap.png)
