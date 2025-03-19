
from django.urls import path
from .views import(
    PostListView,
    PostDetailView,
    IncrementPostView,
    PostHeadingsView,
    GenerateFakeAnalyticsView,
    GenerateFakePostView,
    CategoryListView,
    IncrementCategoryClicksView,
    CategoryDetailView
    ) 

urlpatterns = [
    path('posts/', PostListView.as_view(), name="post-list"),
    path('post/', PostDetailView.as_view(), name="post-detail"),
    path('posts/increment_clicks/', IncrementPostView.as_view(), name="increment-post-click"),
    path('post/headings/', PostHeadingsView.as_view(), name="post-headings"),
    path('generate_post/', GenerateFakePostView.as_view()),
    path('generate_analytics/', GenerateFakeAnalyticsView.as_view()),
    path('categories/', CategoryListView.as_view(), name="category-list"),
    path('category/increment_clicks/', IncrementCategoryClicksView.as_view(), name="increment-category-click"),
    path('category/posts/', CategoryDetailView.as_view(), name="category-posts"),
    
    
]