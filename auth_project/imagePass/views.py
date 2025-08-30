import hashlib
from cryptography.fernet import Fernet
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth import get_user_model
from .forms import ImageLoginForm, RegistrationForm
from .models import HashedImage

User = get_user_model()

def signup_view(request):
    error=""
    if request.method =='POST':
        form = RegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            username = form.cleaned_data['username']
            uploaded_image = form.cleaned_data['image']



            if User.objects.filter(username=username).exists():
                error = "too late, thats someone elses name"
            else:
                user = User.objects.create_user(username=username)
                hashed_image = HashedImage(user=user, image=uploaded_image)
                hashed_image.save()
                login(request, user)
                return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'signup.html', {'form':form, 'error':error})

def image_login_view(request):
    error = ""
    if request.method == 'POST':
        form = ImageLoginForm(request.POST, request.FILES)
        if form.is_valid():
            username = form.cleaned_data['username']
            uploaded_image = form.cleaned_data['image']
            contents = uploaded_image.read()

            image_hash = hashlib.sha256(contents).hexdigest()


            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return render(request, 'login.html', {'form': form, 'error':error})
            try:

                hashed_image = HashedImage.objects.get(user=user)
            except HashedImage.DoesNotExist:
                error = "theres no image registered with this username"
                return render(request, 'login.html', {'form': form, 'error':error})
            if hashed_image.image_hash == image_hash:
                login(request, user)
                return redirect('index')
            else:
                error = "thats the wrong picture"

    else:
        form = ImageLoginForm()
    return render(request, 'login.html', {'form':form, 'error':error})

def index(request):
    return render(request, 'index.html')