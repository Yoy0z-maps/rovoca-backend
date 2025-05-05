# EC2 접속 커멘드

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
