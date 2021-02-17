FROM python:latest
RUN useradd -m k8snotif
WORKDIR /home/k8snotif

COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

ENTRYPOINT ["python", "k8s-watcher.py"]
# CMD can be set for parameters