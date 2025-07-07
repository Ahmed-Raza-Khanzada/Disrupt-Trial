FROM python:3.10

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN apt update && apt install -y curl

COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install --timeout=10000 -r requirements.txt

COPY . /app/

EXPOSE 5001

CMD ["python3", "app.py"]