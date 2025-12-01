from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django import forms

class LoginForm(forms.Form):
    username = forms.CharField(label='Usuario', max_length=150)
    password = forms.CharField(label='Contraseña', widget=forms.PasswordInput)


def login_view(request):
    next_url = request.GET.get('next')
    if not next_url:
        next_url = '/dashboard/'
    if request.user.is_authenticated:
        return redirect(next_url)

    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = authenticate(
            request,
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password']
        )
        if user is not None:
            login(request, user)
            return redirect(next_url)
        else:
            form.add_error(None, 'Usuario o contraseña incorrectos.')
    return render(request, 'users/login.html', {'form': form, 'next': next_url})

def logout_view(request):
    logout(request)
    return redirect('login')
