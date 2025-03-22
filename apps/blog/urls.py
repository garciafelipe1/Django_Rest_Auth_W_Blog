
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
    CategoryDetailView,
    PostCommentViews,
    ListPostCommentsView,
    ListCommentRepliesView,
    CommentReplyViews,
    PostLikeView,
    PostShareView,
    PostAuthorViews,
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
    path('post/comment/', PostCommentViews.as_view()),
    path('post/comments/', ListPostCommentsView.as_view()),
    path('post/comment/replies/', ListCommentRepliesView.as_view()),
    path('post/comment/reply/', CommentReplyViews.as_view()),
    path('post/comment/reply/', CommentReplyViews.as_view()),
    path('post/like/', PostLikeView.as_view()),
    path('post/share/', PostShareView.as_view()),
    path('post/author/',PostAuthorViews.as_view()),
    
    
    
]