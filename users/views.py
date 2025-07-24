# views.py

import requests
import jwt
from jwt import PyJWKClient
from jwt.algorithms import RSAAlgorithm
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User
from .serializers import UserSerializer

APPLE_KEYS_URL = "https://appleid.apple.com/auth/keys"

def verify_kakao_idToken(idToken: str, aud:str):
    try:

        jwks_url = "https://kauth.kakao.com/.well-known/jwks.json"

        # 2. PyJWT의 JWK Client로 서명 검증을 위한 공개키 가져오기
        jwk_client = PyJWKClient(jwks_url)
        signing_key = jwk_client.get_signing_key_from_jwt(idToken)

        # 3. 검증 옵션 설정
        decoded = jwt.decode(
            idToken,
            signing_key.key,
            algorithms=["RS256"],
            audience=aud,             
            issuer="https://kauth.kakao.com" 
        )

        return decoded 

    except jwt.ExpiredSignatureError:
        print("❌ 토큰 만료")
    except jwt.InvalidAudienceError:
        print("❌ Audience(client_id) 불일치")
    except jwt.InvalidIssuerError:
        print("❌ Issuer 불일치")
    except Exception as e:
        print("❌ 토큰 검증 실패:", e)

    return None

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

    print(decoded)

    return {
        "id": decoded["sub"],
        "email": decoded.get("email")
    }


class SocialLoginView(APIView):
    # settings.py에서 DEFAULT_PERMISSION_CLASSES를 정의했기 때문에 소셜 로그인은 AllowAny 권한 필요
    permission_classes = [AllowAny]

    def post(self, request):
        provider = request.data.get("provider")
        credential = request.data.get("result")

        if not provider or not credential:
            return Response({"error": "Missing fields"}, status=400)

        try:
            if provider == "apple":
                user_info = verify_apple_token(credential["identityToken"])
            elif provider == "kakao":
                user_info = verify_kakao_idToken(credential["idToken"], "com.yoy0zmaps.rovoc")
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

        user_data = UserSerializer(user).data

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "is_new_user": created,
            "user": user_data
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
    

from datetime import date
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

class GameStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = date.today()

        if user.last_played_date != today:
            user.play_count = 0
            user.last_played_date = today
            user.save()

        remaining = max(0, 5 - user.play_count)

        return Response({
            "can_play": remaining > 0,
            "remaining": remaining,
            "max": 5
        })
    
class GamePlayView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        today = date.today()

        if user.last_played_date != today:
            user.play_count = 0
            user.last_played_date = today

        if user.play_count >= 5:
            return Response({"can_play": False, "reason": "limit_reached"}, status=403)

        user.play_count += 1
        user.save()

        return Response({
            "can_play": True,
            "remaining": max(0, 5 - user.play_count)
        })
    
class AdRewardView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        today = date.today()

        if user.last_played_date != today:
            user.play_count = 0
            user.last_played_date = today

        if user.play_count >= 10:
            return Response({"can_play": False, "reason": "max_limit_reached"}, status=403)

        # 실제로는 광고 SDK 결과를 검증해야 함 (생략)
        user.play_count += 1
        user.save()

        return Response({
            "can_play": True,
            "remaining": max(0, 10 - user.play_count)
        })

from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from django.db import transaction

class UserDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user

        try:
            with transaction.atomic():
                # 사용자의 모든 토큰을 블랙리스트에 추가
                tokens = OutstandingToken.objects.filter(user=user)
                for token in tokens:
                    BlacklistedToken.objects.get_or_create(token=token)
                
                # 사용자 삭제 (관련된 모든 데이터도 함께 삭제됨)
                user.delete()

            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            print(f"User delete error: {str(e)}")  # 서버 로그에 출력
            return Response(
                {"error": f"사용자 삭제 중 오류가 발생했습니다: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )