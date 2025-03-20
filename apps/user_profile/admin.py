from django.contrib import admin
from django.utils.html import format_html
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display=('user','profile_picture_thumbnail','birthday','website')
    search_fields=('user__username','user__email','biography','website')
    list_filter=('birthday',)
    readonly_fields=('profile_picture_thumbnail','banner_picture_thumbnail')
    ordering=('user__username',)
    fieldsets=(
        ('General Information',{
            'fields':(
                'user',
                'biography',
                'birthday',
                
            )
        }),
        ('Profile Pictures',{
            'fields':(
                'profile_picture',
                'profile_banner',
                
            )
        }),
        ('Social Media Links',{
            'fields':(
                'website',
                'twitter',
                'instagram',
                'github',
                'linkedin',
                'youtube',
                'tiktok',
                'snapchat',
                
            )
        })
    )
    def profile_picture_thumbnail(self, obj):
        if obj.profile_picture and obj.profile_picture.url:
            return format_html('<img src="{}" width="150px" height="auto" />', obj.profile_picture.url)
        return "No Image"
    
    def banner_picture_thumbnail(self, obj):
        if obj.profile_banner and obj.profile_banner.url:
            return format_html('<img src="{}" width="150px" height="auto" />', obj.profile_banner.url)
        else:
            return "No Banner Picture"

    profile_picture_thumbnail.short_description = 'Profile Picture Preview'
    banner_picture_thumbnail.short_description = 'Banner Picture Preview'
