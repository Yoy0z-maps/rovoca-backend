# Social Login 응답 JSON

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

// identityToken Decoding 결과
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
