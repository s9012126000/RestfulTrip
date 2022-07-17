FROM python:3.9.12
WORKDIR /app
COPY requirements.txt /requirements.txt
RUN pip install --user --upgrade pip
RUN pip install --no-cache-dir --user -r /requirements.txt
COPY . .
CMD [ "python3", "-u", "booking_price.py"]