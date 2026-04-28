from django.contrib.auth import authenticate, get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password


User = get_user_model()


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    """
    Body:
    {
      "username": "...",
      "password": "...",
      "email": "..." (optional)
    }
    Returns token so frontend can log in immediately.
    """  

    username = request.data.get("username")
    password = request.data.get("password")
    email = request.data.get("email", "")

    if not username or not password:
        return Response({"detail": "username and password are required."}, status=400)

    if User.objects.filter(username=username).exists():
        return Response({"detail": "username already taken."}, status=400)
    
    try:
        validate_password(password)
    except ValidationError as e:
        return Response({"detail": e.messages}, status=400)

    user = User.objects.create_user(username=username, password=password, email=email)
    token, _ = Token.objects.get_or_create(user=user)

    return Response({"token": token.key}, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    """
    Body:
    {
      "username": "...",
      "password": "..."
    }
    Returns token.
    """
    username = request.data.get("username")
    password = request.data.get("password")

    user = authenticate(username=username, password=password)
    if user is None:
        return Response({"detail": "Invalid credentials."}, status=400)

    Token.objects.filter(user=user).delete()
    token = Token.objects.create(user=user)
    return Response({"token": token.key})

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Deletes token (log out).
    """
    # delete the current user's token
    Token.objects.filter(user=request.user).delete()
    return Response({"detail": "Logged out."})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    """
    Quick endpoint to check who you are.
    """
    return Response({
        "id": request.user.id,
        "username": request.user.username,
        "email": request.user.email,
    })
