FROM python:3.7
RUN useradd comicbetter
WORKDIR /var/lib/comicbetter
RUN mkdir /var/log/comicbetter
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
CMD start_comicbetter
