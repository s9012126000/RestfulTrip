#! /bin/bash
gcloud compute instances stop h1 --zone=asia-east1-b &
gcloud compute instances stop h2 --zone=asia-east1-b &
gcloud compute instances stop a1 --zone=asia-east1-b &
gcloud compute instances stop a2 --zone=asia-east1-b &
gcloud compute instances stop a3 --zone=asia-east1-b &
gcloud compute instances stop b1 --zone=asia-east1-b
