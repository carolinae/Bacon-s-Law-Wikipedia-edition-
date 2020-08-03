FROM python:3

WORKDIR /usr/src/app

EXPOSE 8000

COPY . .

CMD [ "python", "./server.py" ]