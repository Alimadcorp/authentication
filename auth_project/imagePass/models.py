import hashlib
from django.db import models
from cryptography.fernet import Fernet
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

User = get_user_model()

def save_encrypted_uploaded_file(uploaded_file, key: bytes = b'QU6o-n8oTVZwr4IZdIRVwYmXkYtkQ5f5Ezdaa6njUJc='):
    """Encrypt an uploaded file's contents and save via default_storage. Returns (path, hex_sha256)."""
    uploaded_file.seek(0)
    contents = uploaded_file.read()
    image_hash = hashlib.sha256(contents).hexdigest()

    f = Fernet(key)
    encrypted_contents = f.encrypt(contents)

    path = f'encrypted_images/{image_hash}.bin'

    # Save encrypted contents using configured storage (Cloudinary)
    default_storage.save(path, ContentFile(encrypted_contents))
    return path, image_hash


def hash_and_encrypt_upload(instance, filename):

    # This upload_to callable is left for compatibility but should not perform
    # any filesystem writes. It should only compute and return the desired
    # storage path for the uploaded file. Use save_encrypted_uploaded_file from
    # views to actually save encrypted contents to storage.
    uploaded_file = instance.image
    uploaded_file.seek(0)
    contents = uploaded_file.read()

    image_hash = hashlib.sha256(contents).hexdigest()

    path = f'encrypted_images/{image_hash}.bin'

    # Do NOT write to disk or call default_storage.save here. Return only the path.
    return path

class HashedImage(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to=hash_and_encrypt_upload, blank=True)
    image_hash = models.CharField(max_length=64, blank=True)

    def save(self, *args, **kwargs):
        # If image_hash is not provided but image is present, compute hash.
        # If image is a storage-backed file (e.g. already uploaded to Cloudinary),
        # reading it may require contacting the storage backend.
        if self.image and not self.image_hash:
            try:
                self.image.seek(0)
                self.image_hash = hashlib.sha256(self.image.read()).hexdigest()
                self.image.seek(0)
            except Exception:
                # If reading the image fails (e.g. storage issues), fall back
                # to leaving image_hash blank so the save can still proceed.
                pass
        super().save(*args, **kwargs)