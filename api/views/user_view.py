from rest_framework import viewsets
from django.contrib.auth.models import User
from api.serializers import UserSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from .utils import err_no_permission, check_arguments, create_log, err_not_found, err_invalid_input


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def create(self, request):
        if not request.user.is_staff:
            return err_no_permission
        response = check_arguments(request.data, [
            'username',
            'password',
            'first_name',
            'last_name',
            'email',
            'is_staff'
        ])
        if response[0] != 0:
            return response[1]

        username = request.data['username']
        password = request.data['password']
        first_name = request.data['first_name']
        last_name = request.data['last_name']
        email = request.data['email']
        admin = request.data['is_staff'] == "true"

        try:
            User.objects.get(username=username)
            return Response(
                {'message': 'A user with identical username already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except:
            base_user = User.objects.create_user(username=username, password=password,
                                                 first_name=first_name, last_name=last_name,
                                                 email=email)
            base_user.is_staff = admin
            base_user.save()
        Token.objects.create(user=base_user)
        create_log(user=base_user,
                   desc="User %s has been created" % base_user.username)
        return Response(
            {
                'message': 'A user has been created',
                'result': UserSerializer(base_user, many=False).data,
            },
            status=status.HTTP_200_OK
        )

    def list(self, request):
        if not request.user.is_staff:
            return err_no_permission
        queryset = User.objects.all()
        serializer_class = UserSerializer
        return Response(serializer_class(queryset, many=True).data,
                        status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        if pk != request.user.username and not request.user.is_staff:
            return err_no_permission
        queryset = User.objects.all()
        try:
            user = queryset.get(username=pk)
            return Response(
                UserSerializer(user, many=False).data,
                status=status.HTTP_200_OK
            )
        except:
            return err_not_found

    def update(self, request, pk=None):
        if pk != request.user.username and not request.user.is_staff:
            return err_no_permission
        try:
            user = User.objects.get(username=pk)
            if 'first_name' in request.data:
                user.first_name = request.data["first_name"]
            if 'last_name' in request.data:
                user.last_name = request.data["last_name"]
            if 'email' in request.data:
                user.email = request.data["email"]
            if 'is_staff' in request.data:
                user.is_staff = request.data["is_staff"] == "true"
            user.save()
        except:
            return err_not_found
        return Response(
            {'message': 'User has been updated',
             'data': UserSerializer(user, many=False).data},
            status=status.HTTP_200_OK
        )

    @action(methods=['PUT'], detail=True)
    def update_batch(self, request, pk=None):
        if not request.user.is_staff:
            return err_no_permission
        try:
            users = request.data["users"].split(',')
        except:
            return err_invalid_input
        for username in users:
            try:
                user = User.objects.get(username=username)
                if 'first_name' in request.data:
                    user.first_name = request.data["first_name"]
                if 'last_name' in request.data:
                    user.last_name = request.data["last_name"]
                if 'email' in request.data:
                    user.email = request.data["email"]
                if 'is_staff' in request.data:
                    user.is_staff = request.data["is_staff"] == "true"
                user.save()
            except:
                return err_invalid_input
        queryset = User.objects.all()
        return Response(
            UserSerializer(queryset, many=True).data,
            status=status.HTTP_200_OK
        )

    def destroy(self, request, pk=None):
        if not request.user.is_staff:
            return err_no_permission
        try:
            user = User.objects.get(username=pk)
            user.delete()
        except:
            return err_not_found
        return Response({'message': 'User has been deleted'}, status=status.HTTP_200_OK)

    @action(methods=['PUT'], detail=True)
    def change_password(self, request, pk=None):
        if pk != request.user.username and not request.user.is_staff:
            return err_no_permission
        response = check_arguments(request.data, ['password', ])
        if response[0] != 0:
            return response[1]

        queryset = User.objects.all()
        serializer_class = UserSerializer
        username = pk
        password = request.data['password']

        try:
            user = queryset.get(username=username)
            user.set_password(password)
            user.save()
            return Response(
                {
                    'message': 'Password has been set',
                    'result': serializer_class(user, many=False).data
                },
                status=status.HTTP_200_OK,
            )
        except:
            return err_not_found
