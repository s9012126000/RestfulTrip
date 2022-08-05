# [RestfulTrip](https://restful-trip.com/)

**A price comparison website for hotels all over Taiwan, including Hotels.com, Booking.com, and Agoda.**
### Website : https://restful-trip.com/

![](https://i.imgur.com/JzhER9f.png)

## Table of Contents
* [Data Pipeline](#Data-Pipeline)
* [MySQL Schema](#MySQL-Schema)
* [Features](#Features)
* [Technologies](#Technologies)
* [Notification](#Notification)

## Data Pipeline

### 1. Static hotel information
**An ETL pipeline built with Airflow in fetching static hotel information**

![](https://i.imgur.com/4b4oTSE.png)
1. Stored expired data from mongoDB to S3.
2. Fetched hotel information from over Taiwan with web crawler.
3. Stored raw data into MongoDB.
4. Cleaned data and distinguished same hotels from 3 web resources with data_clean pipeline.
5. Transferred cleaned data and monitoring indicators into AWS RDS.
6. Provided views from server built with Flask in EC2.


### 2. Data clean pipeline
**Data clean pipeline is a process of aligning and mapping the same hotels with unmatched names from different web sources in the 5th step of airflow DAG in static hotel information pipeline**
* Examples for unmatched hotels.
<br><img src="https://i.imgur.com/aEoeyZo.png" alt="drawing" width="300"/>


* Compared string similarity using **fuzzy matching** by sequence matcher on hotels' name and address in following 2 rules.
    1. Hotels with names that are almost the same.
       - name matching rate > 0.8
       - address matching rate > 0.2
    2. Hotels with names less matched, and with addresses highly matched.
       - 0.5 < name matching rate < 0.8
       - address matching rate > 0.6


* Steps to compare about 6000+ hotels of each web sources with a stepwise strategy. (2 hundred billion of combinations if using brute force)
![](https://i.imgur.com/ALxHVCb.png)


* An approximate 95%+ of accuracy rate


### 3. Hotels price pipeline
**Hotels price pipeline is a process of updating 14 days of real-time prices on 20k+ hotel websites every day**
* Over 300k of price data are required to be updated every day due to the price fluctuation.


* Managed and monitored price crawler tasks with a producer-consumer pattern by RabbitMQ server which prevents data loss in
advantages of return-confirmed ack process during messages exchange.


* Distributed tasks from message queues to 6 worker machines depending on the type of tasks respectively, and deployed multiple
crawler pods on each worker by Docker images and managed by shell script to enhance scalability.

![](https://i.imgur.com/LP7UrWm.png)

1. Started hotel price pipeline with crontab scheduler 
2. All processes were conducted automatically by executing shell script commands 
   1. Started RabbitMQ server
   2. Produced tasks and transferred them to the respective queue 
   3. Booted all clustered computer
   4. Run all crawler pods built with docker 
   5. Activate queue status listener
3. Once the queues were empty, all tasks had been done, and the queue listener shutdown all nodes


## MySQL Schema
<img src="https://i.imgur.com/693ZEHG.png" alt="drawing" width="350"/>

## Features

### 1. Dashboard for data pipeline monitoring
#### Link: https://restful-trip.com/admin/dashboard
![](https://i.imgur.com/LzhExYg.png)

### 2. Searching on location or hotel name

https://user-images.githubusercontent.com/88102956/181933862-94db3b65-1dec-489d-8727-e81ea01ed366.mp4


### 3. Directly link to the hotel

https://user-images.githubusercontent.com/88102956/183031765-150b4ed8-7759-4921-8fd5-d2d7bab937c0.mp4


## Technologies
### ETL tools
* Airflow
* RabbitMQ
* crontab
* shell script

### Database
* MySQL
* MongoDB

### Cloud service (AWS)
* EC2
* RDS
* S3

### Cloud service (GCP)
* Compute Engine

### Container 
* Docker

### Backend
* Flask

### Frontend
* HTML
* CSS
* JavaScript
* Bootstrap
* Plotly

### Networking
* Nginx
* SSL Certificate

## Notification
> Due to the **cost issue of clustering computing on GCP**, it is unfortunate that the **price pipeline is unable to launch every single day**,  so the price of the hotels may seem to unmatch in RestfulTrip with hotels.com, booking.com, and Agoda
## Contact Me

Jeff Chen:
s9012126000@gmail.com
