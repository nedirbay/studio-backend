import os
import django
import sys

# Add the project directory to the sys.path
sys.path.append('/home/ubuntu/Desktop/Projects/mobile/backend')

# Set the settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studio_api.settings')

# Initialize Django
django.setup()

from blog.models import BlogPost, BlogMedia
from django.utils import timezone

def populate_blogs():
    print("Clearing existing blogs...")
    BlogPost.objects.all().delete()

    blogs_data = [
        {
            'title': 'Foto apparat saýlamagyň 5 syry',
            'main_image': 'https://images.pexels.com/photos/1205033/pexels-photo-1205033.jpeg?auto=compress&cs=tinysrgb&w=800',
            'content': 'Foto apparat saýlamak her bir başlaýjy fotograf üçin iň möhüm ädimdir. Bu makalada biz size dogry saýlaw etmäge kömek etjek 5 sany esasy maslahaty berýäris...\n\n1. Maksadyňyzy kesgitläň.\n2. Megapiksellere däl, matrisanyň ölçegine serediň.\n3. Obýektiwleriň elýeterliligini barlaň.',
            'date': timezone.now().date(),
            'media': [
                {'kind': 'image', 'url': 'https://images.pexels.com/photos/593322/pexels-photo-593322.jpeg?auto=compress&cs=tinysrgb&w=800'}
            ]
        },
        {
            'title': 'Mary şäherinde iň oňat foto-nokatlar',
            'main_image': 'https://images.pexels.com/photos/2582937/pexels-photo-2582937.jpeg?auto=compress&cs=tinysrgb&w=800',
            'content': 'Mary şäheri özüniň taryhy binalary we döwrebap seýilgähleri bilen fotograflar üçin hakyky genji-hazynadyr. Ine, siziň baryp görmeli ýerleriňiz...',
            'date': timezone.now().date(),
            'media': [
                {'kind': 'image', 'url': 'https://images.pexels.com/photos/2100075/pexels-photo-2100075.jpeg?auto=compress&cs=tinysrgb&w=800'}
            ]
        },
        {
            'title': 'Professional suratçy bolmak üçin näme gerek?',
            'main_image': 'https://images.pexels.com/photos/1549000/pexels-photo-1549000.jpeg?auto=compress&cs=tinysrgb&w=800',
            'content': 'Professional suratçy bolmak diňe gowy apparat satyn almak däl. Bu yzygiderli öwreniş we tejribe talap edýär. Biziň merkezimizde geçirilýän okuwlar barada has giňişleýin öwreniň.',
            'date': timezone.now().date(),
            'media': []
        }
    ]

    for b_data in blogs_data:
        media_data = b_data.pop('media', [])
        post = BlogPost.objects.create(**b_data)
        for m in media_data:
            BlogMedia.objects.create(blog=post, **m)
        print(f"Created blog: {post.title}")

if __name__ == '__main__':
    populate_blogs()
    print("Done!")
