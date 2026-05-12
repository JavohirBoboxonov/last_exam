FROM python:3.12-alpine

WORKDIR /java

COPY ./requirements.txt /java/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /java/requirements.txt
ENV PYTHONPATH=/code

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]