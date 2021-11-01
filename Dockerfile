FROM python:3
ADD uottawa-gym-scheduler.py /
ADD gym.txt /
RUN pip install requests
RUN pip install bs4
RUN pip install pandas
RUN pip install schedule
RUN pip install threaded
RUN pip install datetime
RUN pip install lxml
RUN echo "America/Toronto" > /etc/timezone
CMD [ "python", "./uottawa-gym-scheduler.py" ]
