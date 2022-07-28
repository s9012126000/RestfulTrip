#!/bin/bash

sudo docker start myrabbitmq

source /home/s9012126000_gmail_com/miniconda3/etc/profile.d/conda.sh

cd ../ && conda activate personal
python3 send_msg.py

gcloud compute instances start h1 --zone=asia-east1-b &
gcloud compute instances start h2 --zone=asia-east1-b &
gcloud compute instances start a1 --zone=asia-east1-b &
gcloud compute instances start a2 --zone=asia-east1-b &
gcloud compute instances start a3 --zone=asia-east1-b &
gcloud compute instances start b1 --zone=asia-east1-b &
sleep 20
wait -f
gcloud compute ssh h1 --zone=asia-east1-b -- 'sudo docker start h1' &
gcloud compute ssh h2 --zone=asia-east1-b -- 'sudo docker start h1' &
gcloud compute ssh a1 --zone=asia-east1-b -- 'sudo docker start a1' &
gcloud compute ssh a2 --zone=asia-east1-b -- 'sudo docker start a1' &
gcloud compute ssh a3 --zone=asia-east1-b -- 'sudo docker start a1' &
gcloud compute ssh b1 --zone=asia-east1-b -- 'sudo docker start b1' &
sleep 10
wait -f
python3 queue_tracker.py &
