import os
import time
from django.conf import settings

class CleanupMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        self.cleanup_old_files()
        return response

    def cleanup_old_files(self):
        """Remove files older than the specified age from the media directory."""
        age_limit = 3600  # 1 hour in seconds
        now = time.time()

        # Get all files in the media directory
        for filename in os.listdir(settings.MEDIA_ROOT):
            file_path = os.path.join(settings.MEDIA_ROOT, filename)

            # Check if it's a file and if it's older than the age limit
            if os.path.isfile(file_path):
                file_age = now - os.path.getmtime(file_path)
                if file_age > age_limit:
                    os.remove(file_path)
