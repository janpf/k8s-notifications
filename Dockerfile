FROM python:latest

COPY requirements.txt /home/requirements.txt
WORKDIR /home
RUN pip install -r requirements.txt
COPY . /home

ENTRYPOINT ["python", "k8s-watcher.py"]
# CMD can be set for parameters