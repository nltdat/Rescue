# Generated manually for data cleaning

from django.db import migrations


def remove_duplicate_phones(apps, schema_editor):
    """
    Find users with duplicate phone numbers and set phone to NULL for duplicates.
    Keep the first user with each phone number.
    """
    User = apps.get_model('users', 'User')
    
    # Get all phone numbers that appear more than once
    from django.db.models import Count
    phone_counts = User.objects.values('phone').annotate(
        count=Count('id')
    ).filter(count__gt=1, phone__isnull=False).exclude(phone='')
    
    for item in phone_counts:
        phone = item['phone']
        users_with_phone = User.objects.filter(phone=phone).order_by('id')
        
        # Keep the first user's phone, clear others
        for user in users_with_phone[1:]:
            user.phone = None
            user.save()


def reverse_migration(apps, schema_editor):
    # Cannot reverse this migration
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_user_profile_image_alter_user_phone'),
    ]

    operations = [
        migrations.RunPython(remove_duplicate_phones, reverse_migration),
    ]
