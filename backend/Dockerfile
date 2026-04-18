FROM mcr.microsoft.com/playwright/python:v1.52.0-noble

WORKDIR /app/backend

RUN apt-get update && apt-get install -y --no-install-recommends nodejs npm && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN npm install -g @modelcontextprotocol/inspector
RUN playwright install chromium

COPY . /app/backend

EXPOSE 8000

CMD ["python", "launch_public.py"]
