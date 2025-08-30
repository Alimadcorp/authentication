import hashlib
from cryptography.fernet import Fernet
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth import get_user_model
from .forms import ImageLoginForm
from .forms import RegistrationForm
from .models import HashedImage
from django.contrib.auth.decorators import login_required
from .forms import starSightingForm
from .models import starSighting

User = get_user_model()

def signup_view(request):
    error = ""
    if request.method == 'POST':
        form = RegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            username = form.cleaned_data['username']
            uploaded_image = form.cleaned_data['image']

            if User.objects.filter(username=username).exists():
                error = "too late, thats someone elses name"
            else:
                user = User.objects.create_user(username=username)
                # Save only the encrypted contents to configured storage (Cloudinary)
                from .models import save_encrypted_uploaded_file
                path, image_hash = save_encrypted_uploaded_file(uploaded_image)

                # Create HashedImage and point ImageField to the already-saved encrypted file
                hashed_image = HashedImage(user=user)
                hashed_image.image.name = path
                hashed_image.image_hash = image_hash
                hashed_image.save()

                login(request, user)
                return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'signup.html', {'form': form, 'error': error})

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

@login_required
def star(request):
    if request.method == 'POST':
        form = starSightingForm(request.POST)
        if form.is_valid():
            star_sighting = form.save(commit=False)
            star_sighting.user = request.user
            star_sighting.save()
            print(f"saved star sighting: {star_sighting.star_name} for user {star_sighting.user}")
            return redirect('star')
    else:
        form = starSightingForm()
    sightings = starSighting.objects.filter(user=request.user).order_by('-date_seen')
    return render(request, 'star.html', {'form': form, 'sightings': sightings})

def index(request):
    return render(request, 'index.html')