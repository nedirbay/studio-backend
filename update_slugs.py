import os
import django
import sys
from django.utils.text import slugify

# Add the project directory to the sys.path
sys.path.append('/home/ubuntu/Desktop/Projects/mobile/backend')

# Set the settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studio_api.settings')

# Initialize Django
django.setup()

from blog.models import BlogPost

def generate_slugs():
    posts = BlogPost.objects.filter(slug__isnull=True) | BlogPost.objects.filter(slug='')
    print(f"Generating slugs for {posts.count()} posts...")
    for post in posts:
        post.slug = slugify(post.title)
        post.save()
        print(f"Updated: {post.title} -> {post.slug}")

if __name__ == '__main__':
    generate_slugs()
    print("Done!")
