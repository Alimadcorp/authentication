import hashlib
from django.db import models
from cryptography.fernet import Fernet
import os
from django.contrib.auth import get_user_model

User = get_user_model()

def hash_and_encrypt_upload(instance, filename):

    uploaded_file = instance.image
    contents = uploaded_file.read()

    image_hash = hashlib.sha256(contents).hexdigest()

    key = b'QU6o-n8oTVZwr4IZdIRVwYmXkYtkQ5f5Ezdaa6njUJc='
    f = Fernet(key)
    encrypted_contents = f.encrypt(contents)

    path = f'encrypted_images/{image_hash}.bin'
    full_path = os.path.join('media', path)

    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    with open(full_path, 'wb') as file:
        file.write(encrypted_contents)
    return path

class HashedImage(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to=hash_and_encrypt_upload)
    image_hash = models.CharField(max_length=64, blank=True)

    def save(self, *args, **kwargs):
        if self.image and not self.image_hash:
            self.image.seek(0)
            self.image_hash = hashlib.sha256(self.image.read()).hexdigest()
            self.image.seek(0)
            super().save(*args, **kwargs)