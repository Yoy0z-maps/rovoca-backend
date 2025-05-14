# EC2 접속 커멘드 Amazon Linux 2

```bash
ssh -i "rovoca.pem" ec2-user@ec2-54-180-57-195.ap-northeast-2.compute.amazonaws.com
```

# Social Login 응답 JSON

- Kakao Authentication

```json
// API 응답결과
{
  "accessToken": "kqqKCpFsUJR",
  "accessTokenExpiresAt": 1746496678.8926458,
  "accessTokenExpiresIn": 43199,
  "idToken": "eyJraWQl8tp_sJM_ENwUanTq-qbyksyZXTtEv-ocfSE9DDSS6ZlQ",
  "refreshToken": "NoKcgIocdXwhKCpFsUJR",
  "refreshTokenExpiresAt": 1751637478.892648,
  "refreshTokenExpiresIn": 5183999,
  "scopes": [],
  "tokenType": "bearer"
}

// idToken BASE64 Decoding
{
  "aud": "NATIVE_APP_KEY",
  "sub": "user_unique_id",
  "auth_time": 1746453479,
  "iss": "https://kauth.kakao.com",
  "exp": 1746496679,
  "iat": 1746453479
}
```

- Apple Authentication

```json
// API 응답 결과
{
  "authorizationCode": "ce45...X5ZvQ",
  "email": "abcd1234@gmail.com",
  "fullName": {
    "familyName": null,
    "givenName": null,
    "middleName": null,
    "namePrefix": null,
    "nameSuffix": null,
    "nickname": null
  },
  "identityToken": "eyJraWQiOiJ...Xww", // JWT 형식
  "realUserStatus": 1,
  "state": null,
  "user": "324.....2312"
}

// identityToken BASE64 Decoding
{
    "iss": "https://appleid.apple.com",
    "aud": "....",
    "exp": 17.....6205,
    "iat": 1....5,
    "sub": "0....316",
    "c_hash": "cu21SV......QxQ",
    "email": "gksdygks2124@gmail.com",
    "email_verified": true,
    "auth_time": 17.....5,
    "nonce_supported": true
}
```

# Gunicorn 설치 및 설정

```bash
pip install gunicorn # venv 활성 상태
gunicorn django_app_name.wsgi:application --bind 127.0.0.1:8000 # 실행 테스트

# Gunicorn systemd 서비스 등록 (내용은 아래 참고)
sudo nano /etc/systemd/system/gunicorn.service

sudo systemctl daemon-reexec # systemd 재시작 명령어
sudo systemctl daemon-reload # systemd가 서비스 파일 변경 내용을반영하도록 강제 리로드
sudo systemctl start gunicorn # 재시작 명령어
sudo systemctl enable gunicorn # 부팅 시 자동으로 gunicorn 서비스를 항상 실행되도록 등록
sudo systemctl status gunicorn # status 확인
```

```ini
[Unit]
Description=gunicorn daemon for rovoca
After=network.target

[Service]
User=nginx
Group=nginx
WorkingDirectory=/home/ec2-user/rovoca-backend
ExecStart=/home/ec2-user/rovoca-backend/venv/bin/gunicorn --access-logfile - --workers 3 --bind unix:/home/ec2-user/rovoca-backend/gunicorn.sock rovoca.wsgi:application

[Install]
WantedBy=multi-user.target
```

# Nginx 설치 및 설정

```bash
sudo dnf install nginx -y  # 설치
nginx -v # 설치 확인

# Nginx 실행 및 부팅 등록
sudo systemctl start nginx
sudo systemctl enable nginx

# Nginx 사이트 설정
sudo nano /etc/nginx/conf.d/rovoca.conf

# Nginx 설정 테스트 & 적용
sudo nginx -t
# nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
# nginx: configuration file /etc/nginx/nginx.conf test is successful
```

```nginx
server {
    listen 80;
    server_name api.rovoca.site;

    # 정적 파일 서빙
    location /static/ {
        alias /home/ec2-user/rovoca-backend/static/;
    }

    location /media/ {
        alias /home/ec2-user/rovoca-backend/media/;
    }

    # Gunicorn 유닉스 소켓에 프록시 연결
    location / {
        proxy_pass http://unix:/home/ec2-user/rovoca-backend/gunicorn.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

# HTTPS 인증서 발급

```bash
# certbot 설치
sudo dnf install certbot python3-certbot-nginx -y
# HTTPS 인증서 발급 및 자동 설정
sudo certbot --nginx -d api.rovoca.site
# 자동 갱신 (90일 만료))
sudo dnf install cronie -y
sudo crontab -l
```
