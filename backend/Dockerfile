# 1단계: base 이미지
FROM python:3.10

# 2단계: 작업 디렉토리 지정
WORKDIR /app

# 3단계: requirements 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .


EXPOSE 8000

# 7단계: 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

