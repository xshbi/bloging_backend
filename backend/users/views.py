from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import redirect
from django.contrib.auth import update_session_auth_hash
from .models import User
from .serializers import (
    UserSerializer,
    RegisterSerializer,
    UserPublicSerializer,
    ChangePasswordSerializer
)

class RegisterView(generics.CreateAPIView):
    """Anyone can register"""
    queryset            = User.objects.all()
    serializer_class    = RegisterSerializer
    permission_classes  = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # generate JWT tokens on register
        refresh = RefreshToken.for_user(user)
        return Response({
            'user'   : UserSerializer(user).data,
            'access' : str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_201_CREATED)


class ProfileView(generics.RetrieveUpdateAPIView):
    """Get or update logged in user's own profile"""
    serializer_class   = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class PublicProfileView(generics.RetrieveAPIView):
    """Get any user's public profile by username"""
    serializer_class   = UserPublicSerializer
    permission_classes = [permissions.AllowAny]
    queryset           = User.objects.all()
    lookup_field       = 'username'


class ChangePasswordView(APIView):
    """Change password for logged in user"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {'error': 'Old password is incorrect.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(serializer.validated_data['new_password'])
        user.save()
        update_session_auth_hash(request, user)
        return Response({'message': 'Password changed successfully.'})


class LogoutView(APIView):
    """Blacklist the refresh token on logout"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data['refresh']
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Logged out successfully.'})
        except Exception:
            return Response(
                {'error': 'Invalid token.'},
                status=status.HTTP_400_BAD_REQUEST
            )


class AllUsersView(generics.ListAPIView):
    """Admin only — list all users"""
    queryset           = User.objects.all().order_by('-date_joined')


from rest_framework.authentication import SessionAuthentication

class OAuthSuccessView(APIView):
    """Generates JWT and redirects to frontend app"""
    authentication_classes = [SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)
        return redirect(f"http://localhost:5173/?access={access}&refresh={refresh}")