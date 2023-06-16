FROM python:3.10-alpine

WORKDIR /app

COPY requirements.txt .

RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip install --no-cache-dir -r requirements.txt

COPY ./*.py /app

EXPOSE 5000

CMD ["gunicorn","-b","0.0.0.0:5000","app:app"]
