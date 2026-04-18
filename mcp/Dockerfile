FROM mcr.microsoft.com/playwright/python:v1.52.0-noble

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN npm install -g @modelcontextprotocol/inspector
RUN playwright install chromium

COPY . .

EXPOSE 8000

CMD ["python", "launch_public.py"]
