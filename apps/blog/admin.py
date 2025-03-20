from django.contrib import admin
from .models import (
    Category,
    Post,Heading
    ,PostAnalytics,
    CategoryAnalytics,
    PostInteraccion,
    PostLike,
    PostShare,
    Comment,
    PostView
)
from django.utils.html import format_html

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "title","parent", "slug")
    search_fields = ("name", "title", "description","slug")
    prepopulated_fields = {"slug": ("name",)}
    list_filter = ("parent",)
    ordering=("name",)
    readonly_fields=('id',)

@admin.register(CategoryAnalytics)
class CategoryAnalyticsAdmin(admin.ModelAdmin):
    list_display=('category_name','views','impressions','clicks','click_through_rate','avg_time_on_page')
    search_fields=('category__name',)
    readonly_fields=('category','views','impressions','clicks','click_through_rate','avg_time_on_page')
    
    def category_name(self,obj):
        return obj.category.name
    
    category_name.short_description='Category Name'
    


class HeadingInline(admin.TabularInline):
    model=Heading
    extra=1
    fields=('title','level','order','slug')
    prepopulated_fields={"slug":("title",)}
    ordering=('order',)

# class MediaInline(admin.TabularInline):
#     model=Post.media
#     fields=('media',)
#     extra=1

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display=('title','status','category','created_at','update_at','mostrar_thumbnail')
    search_fields=('title','description','content','keywords','slug')
    prepopulated_fields = {"slug": ("title",)}
    list_filter=('status','category','update_at')
    ordering=('-created_at',)
    readonly_fields=('id','created_at','update_at')
    fieldsets=(
        ('General Information',{
            'fields':(
                'title',
                'description',
                'content',
                'thumbnail',
                'keywords',
                'slug',
                'category',
                'user',
            )
        }),
        ('Status & Date',{
            'fields':(
                'status',
                'created_at',
                'update_at',
            )
            
        })
    )
    inlines=[HeadingInline]
    def mostrar_thumbnail(self, obj):
        if obj.thumbnail:
            return format_html('<img src="{}" width="150px"; height="auto;" />', obj.thumbnail.url)
        else:
            return "No Thumbnail"

    mostrar_thumbnail.short_description = 'Thumbnail'

# @admin.register(Heading)
# class HeadingAdmin(admin.ModelAdmin):
#     list_display=('title','post','level','order')
#     search_fields=('title','post__title')
#     list_filter=('level','post')
#     ordering=('post','order')
#     prepopulated_fields=({"slug":("title",)})
    

@admin.register(PostAnalytics)
class PostAnalyticsAdmin(admin.ModelAdmin):
    list_display=('post_title','views','impressions','clicks','click_through_rate','avg_time_on_page','likes','comments','shares')
    search_fields=('post__title','post__slug')
    readonly_fields=('views','impressions','clicks','click_through_rate','avg_time_on_page','likes','comments','shares')
    
    def post_title(self,obj):
        return obj.post.title
    
    post_title.short_description='Post title'
    
    

@admin.register(PostInteraccion)
class PostInteraccionAdmin(admin.ModelAdmin):
    list_display=('user','post','interaction_type','timestamp')
    search_fields=('user__username','post__title','interaction_type')
    list_filter=('interaction_type','timestamp')
    ordering=('-timestamp',)
    readonly_fields=('id','timestamp')

    def post_title(self,obj):
        return obj.post.title
    
    post_title.short_description='Post title'

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display=('id','user','post','parent','created_at','update_at','is_active')
    search_fields=('user__username','post__title','content')
    list_filter=('is_active','created_at','update_at')
    ordering=('-created_at',)
    readonly_fields=('id','created_at','update_at')
    list_select_related=('user','post','parent')
    fieldsets=(
        ('General Information',{
            'fields':(
                'user',
                'post',
                'parent',
                'content',
            )
        }),
        ('Status & Date',{
            'fields':(
                'is_active',
                'created_at',
                'update_at',
            )
            
        })
    )


@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display=('id','user','post','timestapm')
    search_fields=('user__username','post__title')
    list_filter=('timestapm',)
    ordering=('-timestapm',)
    readonly_fields=('id','timestapm')
    list_select_related=('user','post') 
    fieldsets=(
        ("General Information",{
            'fields':(
                'user',
                'post',
            )
        }),
        ('Status & Date',{
            'fields':(
                'timestapm',
            )}),
    )
    
@admin.register(PostShare)
class PostShareAdmin(admin.ModelAdmin):
    list_display=('id','user','post','plataform','timestapm')
    search_fields=('user__username','post__title','plataform')
    list_filter=('plataform','timestapm',)
    ordering=('-timestapm',)
    readonly_fields=('id','timestapm')
    list_select_related=('user','post') 
    fieldsets=(
        ("General Information",{
            'fields':(
                'user',
                'post',
                'plataform',
            )
        }),
        ('Status & Date',{
            'fields':(
                'timestapm',
            )}),
    )
    
@admin.register(PostView)
class PostViewAdmin(admin.ModelAdmin):
    list_display=('id','user','post','ip_address','timestamp',)
    search_fields=('user__username','post__title','ip_address')
    list_filter=('timestamp',)
    ordering=('-timestamp',)
    readonly_fields=('id','timestamp',)
    list_select_related=('user','post') 
    fieldsets=(
        ("General Information",{
            'fields':(
                'user',
                'post',
                'ip_address',
            )
        }),
        ('Status & Date',{
            'fields':(
                'timestamp',
            )}),
    )
    
