FROM python:3.12-slim

WORKDIR /app

COPY api/requirements.txt .

RUN pip install -r requirements.txt

COPY api/ .

COPY libs/ libs/

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
