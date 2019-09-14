cat Dockerfile
FROM python:3.7
RUN useradd comicbetter
WORKDIR /var/lib/comicbetter
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY start_comicbetter ./
RUN chown -R comicbetter:comicbetter ./
USER comicbetter
CMD start_comicbetter
