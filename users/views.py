# views.py

import requests
import jwt
from jwt.algorithms import RSAAlgorithm
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User
from .serializers import UserSerializer


APPLE_KEYS_URL = "https://appleid.apple.com/auth/keys"


def verify_apple_token(identity_token: str):
    res = requests.get(APPLE_KEYS_URL)
    apple_keys = res.json()["keys"]
    headers = jwt.get_unverified_header(identity_token)
    kid = headers["kid"]
    alg = headers["alg"]

    key = next((k for k in apple_keys if k["kid"] == kid and k["alg"] == alg), None)
    if key is None:
        raise Exception("Apple public key not found")

    public_key = RSAAlgorithm.from_jwk(key)

    decoded = jwt.decode(
        identity_token,
        key=public_key,
        algorithms=[alg],
        audience="com.yoy0zmaps.rovoc",
        issuer="https://appleid.apple.com"
    )

    return {
        "id": decoded["sub"],
        "email": decoded.get("email")
    }


class SocialLoginView(APIView):
    def post(self, request):
        provider = request.data.get("provider")
        token = request.data.get("access_token")

        if not provider or not token:
            return Response({"error": "Missing fields"}, status=400)

        try:
            if provider == "apple":
                user_info = verify_apple_token(token)
            else:
                return Response({"error": "Unsupported provider"}, status=400)
        except Exception as e:
            return Response({"error": str(e)}, status=401)

        # 유저 찾거나 생성
        user, created = User.objects.get_or_create(
            provider=provider,
            social_id=user_info["id"],
            defaults={"nickname": "temp"}
        )

        # JWT 발급
        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "is_new_user": created
        })
    
from rest_framework.generics import UpdateAPIView
from .models import User
from .serializers import UserSerializer

class UserProfileUpdateView(UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
    

# views.py
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import UserSerializer

class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)