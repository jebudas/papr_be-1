from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout


def signup(request):

    if request.method == 'POST':

        if request.POST['password1'] == request.POST['password2']:

            try:

                user = User.objects.get(username=request.POST['username'])

                return render(request, 'accounts/signup.html', {'error':'User already exists!'})

            except User.DoesNotExist:

                user = User.objects.create_user(request.POST['username'], password=request.POST['password1'])

                if user is not None:

                    login(request, user)

                    return redirect('home')

        else:

            return render(request, 'accounts/signup.html', {'error':'Passwords did not match'})


    else:
        return render(request, 'accounts/signup.html')


def loginUser(request):

    if request.method == 'POST':

        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:

            login(request, user)

            if 'next' in request.POST:
                return redirect(request.POST['next'])
            else:
                return redirect('home')


        else:

            return render(request, 'accounts/loginUser.html', {'error':'Hahaha, nice try but that user is nope.'})

    else:

        return render(request, 'accounts/loginUser.html')

def logoutUser(request):

    if request.method == 'POST':

        logout(request)

        return redirect('home')
