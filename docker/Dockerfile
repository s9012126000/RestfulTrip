FROM python:3.9.12
WORKDIR /app
COPY requirements.txt /requirements.txt
RUN pip install --user --upgrade pip
RUN pip install --no-cache-dir --user -r /requirements.txt
RUN apt-get update -y
RUN apt-get install -y wget
RUN wget -q https://dl.google.com/linux/direct/google-chrome-beta_current_amd64.deb
RUN dpkg --unpack ./google-chrome-beta_current_amd64.deb
RUN apt-get install -f -y
#RUN sudo apt-get install ./google-chrome-beta_current_amd64.deb
COPY . .
CMD [ "python3", "test.py"]