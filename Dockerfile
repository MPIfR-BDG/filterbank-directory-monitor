FROM python:3.6
USER root
WORKDIR /app
ADD . /app
RUN pip install -r requirements.txt
EXPOSE 8050
CMD ["python", "app.py"]