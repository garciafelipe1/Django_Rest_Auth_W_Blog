from rest_framework_api.views import StandardAPIView,APIView
from rest_framework.exceptions import NotFound,APIException,ValidationError
from django.conf import settings
from django.core.cache import cache
from rest_framework import permissions
from django.db.models.functions import Coalesce
from django.db.models import Q,F,Value
from rest_framework import status

import redis

from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import (
    Post,
    Heading,
    PostAnalytics,
    Category,
    CategoryAnalytics,
    PostView,
    PostInteraccion,
    Comment,
    PostLike,
    PostShare,
)
from .serializers import (
    PostSerializer,
    PostListSerializer,
    HeadingSerializer,
    CategoryListSerializer,
    CommentSerializer
    
    )
from .utils import get_client_ip
from .tasks import increment_post_views_task
from django.db.models import Prefetch
from apps.authentication.models import UserAccount
from faker import Faker
from utils.string_utils import sanitize_string,sanitize_html

import random
import uuid
from django.utils.text import slugify
from rest_framework.pagination import PageNumberPagination

redis_client=redis.Redis(host=settings.REDIS_HOST,port=6379,db=0)


class PostAuthorViews(StandardAPIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user=request.user
        if user.role == "customer":
            return self.error("you do noy have permission to create post")
        
        posts = Post.objects.filter(user=user)
        
        if not posts.exists():
            raise NotFound(detail="No posts found")
        
        
        serialized_post=PostListSerializer(posts,many=True).data
        
        
        return self.paginate(request,serialized_post)


    def put(self, request):
        
        user=request.user
        if user.role == "customer":
            return self.error("you do noy have permission to create post")
        
        post_slug=request.data.get("post_slug",None)
        
        if not post_slug:
            raise NotFound(detail="Post slug  must be provided")
        
        try:
            post = Post.objects.get(slug=post_slug,user=user)
        except Post.DoesNotExist:
            raise NotFound(f"Post {post_slug} does not exist.")
        
        title=sanitize_string(request.data.get("title",None))
        description = sanitize_string(request.data.get("description", None))
        content=sanitize_html(request.data.get("content",None))
        post_status=sanitize_string(request.data.get("status","draft"))
        category_slug=slugify(request.data.get("category",post.category.slug))
        
        
        if category_slug:
            try:
                category=Category.objects.get(slug=category_slug)
            except Category.DoesNotExist:
                return self.error(f"Category '{category_slug}' does not exist",status=400)
            
            post.category=category
 
        if title:
            post.title=title
        
        if description is not None:
            post.description = description
        
        if content:
            post.content=content
        
        
        
        post.status=post_status
        
        headings=request.data.get("headings",[])
        if headings:
            post.headings.all().delete()
            for heading_data in headings:
                Heading.objects.create(
                    post=post,
                    title=heading_data.get("title"),
                    level=heading_data.get("level"),
                    order=heading_data.get("order"),
                )
        
        post.save()
        
        
        return self.response(f"post {post.title} updated successfuly")
      
    def post(self, request):
        
        user=request.user
        if user.role == "customer":
            return self.error("you do noy have permission to create post")
        
        
        required_fields = ["title","content", "slug", "category"]
        
        missing_fields = [field for field in required_fields if not request.data.get(field)]
        
        if missing_fields:
            return self.error(f"Missing required fields: {', '.join(missing_fields)}")
        
        
        title=sanitize_string(request.data.get("title",None))
        description=sanitize_string(request.data.get("description",""))
        content=sanitize_html(request.data.get("content",None))
        
        keywords=sanitize_string(request.data.get("keywords",""))
        slug=slugify(request.data.get("slug",None))
        category_slug=slugify(request.data.get("category",None))
        
        try:
            category=Category.objects.get(slug=category_slug)
        except Category.DoesNotExist:
            return self.error(f"Category '{category_slug}' does not exist",status=400)
        
        try:
            post =Post.objects.create(
                user=user,
                title=title,
                description=description,
                content=content,
                keywords=keywords,
                slug=slug,
                category=category
            )
            
        
            headings=request.data.get("headings",[]) 
            for heading_data in headings:
                Heading.objects.create(
                    post=post,
                    title=heading_data.get("title"),
                    slug=heading_data.get("slug"),
                    level=heading_data.get("level"),
                    order=heading_data.get("order")
                )
                 
        except Exception as e:
            return self.error(f"Error creating post: {str(e)}")
  
        return self.response(f"Post '{post.title}' created successfully")
    
    
    def delete(self, request):
        user=request.user
        if user.role == "customer":
            return self.error("you do noy have permission to create post")
        
        post_slug=request.query_params.get("slug",None)
        
        if not post_slug:
            raise NotFound(detail="Post slug  must be provided")
        
        try:
            post = Post.objects.get(slug=post_slug,user=user)
        except Post.DoesNotExist:
            raise NotFound(f"Post {post_slug} does not exist.")
        
        post.delete()
        
        
        
        return self.response(f"post {post.title} deleted successfuly")

class PostPagination(PageNumberPagination):
    page_size = 10  
    page_size_query_param = 'page_size'
    max_page_size = 50  


class PostListView(StandardAPIView):
    

    def get(self, request, *args, **kwargs):
        try:
            # Parametros de solicitud
            search = request.query_params.get("search", "").strip()
            sorting = request.query_params.get("sorting", None)
            ordering = request.query_params.get("ordering", None)
            author = request.query_params.get("author", None)
            is_featured = request.query_params.get("is_featured", None)
            categories = request.query_params.getlist("categories", [])
            page = request.query_params.get("p", "1")

            # Construir clave de cache para resultados paginados
            cache_key = f"post_list:{search}:{sorting}:{ordering}:{author}:{categories}:{is_featured}:{page}"
            cached_posts = cache.get(cache_key)
            if cached_posts:
                # Serializar los datos del caché
                serialized_posts = PostListSerializer(cached_posts, many=True).data
                # Incrementar impresiones en Redis para los posts del caché
                for post in cached_posts:
                    redis_client.incr(f"post:impressions:{post.id}")  # Usar `post.id`
                return self.paginate(request, serialized_posts)

            # Consulta inicial optimizada con nombres de anotación únicos
            posts = Post.postobjects.all().select_related("category").annotate(
                analytics_views=Coalesce(F("post_analytics__views"), Value(0)),
                analytics_likes=Coalesce(F("post_analytics__likes"), Value(0)),
                analytics_comments=Coalesce(F("post_analytics__comments"), Value(0)),
                analytics_shares=Coalesce(F("post_analytics__shares"), Value(0)),
            )
            
            # Filtrar por autor
            if author:
                posts = posts.filter(user__username=author)

            # Si no hay posts del autor, responder inmediatamente
            if not posts.exists():
                raise NotFound(detail=f"No posts found for author: {author}")
            
            # Filtrar por busqueda
            if search:
                posts = posts.filter(
                    Q(title__icontains=search) |
                    Q(description__icontains=search) |
                    Q(content__icontains=search) |
                    Q(keywords__icontains=search) |
                    Q(category__name__icontains=search)
                )
            
            # Filtrar por categoria
            if categories:
                category_queries = Q()
                for category in categories:
                    # Check if category is a valid uuid
                    try:
                        uuid.UUID(category)
                        uuid_query = (
                            Q(category__id=category)
                        )
                        category_queries |= uuid_query
                    except ValueError:
                        slug_query = (
                            Q(category__slug=category)
                        )
                        category_queries |= slug_query
                posts = posts.filter(category_queries)
            
            # Filtrar por posts destacados
            if is_featured:
                # Convertir el valor del parámetro a booleano
                is_featured = is_featured.lower() in ['true', '1', 'yes']
                posts = posts.filter(featured=is_featured)
            
            # Ordenamiento
            if sorting:
                if sorting == "newest":
                    posts = posts.order_by("-created_at")
                elif sorting == 'az':
                    posts = posts.order_by("title")
                elif sorting == 'za':
                    posts = posts.order_by("-title")
                elif sorting == "recently_updated":
                    posts = posts.order_by("-updated_at")
                elif sorting == "most_viewed":
                    posts = posts.order_by("-analytics_views") 

            # if ordering:

            # Guardar los objetos en el caché
            cache.set(cache_key, posts, timeout=60 * 5)

            # Serializar los datos para la respuesta
            serialized_posts = PostListSerializer(posts, many=True).data

            # Incrementar impresiones en Redis
            for post in posts:
                redis_client.incr(f"post:impressions:{post.id}")  # Usar `post.id`

            return self.paginate(request, serialized_posts)
        except NotFound as e:
            return self.response([], status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            raise APIException(detail=f"An unexpected error occurred: {str(e)}")
class PostDetailView(StandardAPIView):
    

    def get(self, request):
        ip_address = get_client_ip(request)
        slug = request.query_params.get("slug")
        user = request.user if request.user.is_authenticated else None

        if not slug:
            raise NotFound(detail="A valid slug must be provided")

        try:
            # Verificar si los datos están en caché
            cache_key = f"post_detail:{slug}"
            cached_post = cache.get(cache_key)
            if cached_post:
                serialized_post = PostSerializer(cached_post, context={'request': request}).data
                self._register_view_interaction(cached_post, ip_address, user)
                return self.response(serialized_post)

            # Si no está en caché, obtener el post de la base de datos
            try:
                post = Post.objects.get(slug=slug)
            except Post.DoesNotExist:
                raise NotFound(f"Post {slug} does not exist.")

            serialized_post = PostSerializer(post, context={'request': request}).data

            # Guardar en el caché
            cache.set(cache_key, post, timeout=60 * 5)

            # Registrar interaccion
            self._register_view_interaction(post, ip_address, user)
            

        except Post.DoesNotExist:
            raise NotFound(detail="The requested post does not exist")
        except Exception as e:
            raise APIException(detail=f"An unexpected error occurred: {str(e)}")

        return self.response(serialized_post)
    def _register_view_interaction(self, post, ip_address, user):
        """
        Registra la interacción de tipo 'view', maneja incrementos de vistas únicas 
        y totales, y actualiza PostAnalytics.
        """
        # Verifica si esta IP y usuario ya registraron una vista única
        if not PostView.objects.filter(post=post, ip_address=ip_address, user=user).exists():
            # Crea un registro de vista unica
            PostView.objects.create(post=post, ip_address=ip_address, user=user)

            try:
                PostInteraccion.objects.create(
                    user=user,
                    post=post,
                    interaction_type="view",
                    ip_address=ip_address,
                )
            except Exception as e:
                raise ValueError(f"Error creeating PostInteraction: {e}")

            analytics, _ = PostAnalytics.objects.get_or_create(post=post)
            analytics.increment_metric('views')
           

class PostHeadingsView(APIView):
    serializer_class=HeadingSerializer
    
    
    def get(self,request):
        post_slug=request.query_params.get("slug")
        heading_objects=Heading.objects.filter(post__slug=post_slug)
        serializer_data=HeadingSerializer(heading_objects,many=True).data
        return Response(serializer_data)
    # def get_queryset(self):
    #     post_slug=self.kwargs['slug']
    #     return Heading.objects.filter(post__slug=post_slug)



class IncrementPostView(APIView):
    
    def post(self,request):
        
        
        data=request.data
        try:
            post=Post.postobjects.get(slug=data['slug'])
        except Post.DoesNotExist:
            raise NotFound(detail="the requested post does not exist")
             
        try:
            post_analytics, created = PostAnalytics.objects.get_or_create(post=post)
            post_analytics.increment_clicks()  # Correcto: sin argumentos adicionales
        except Exception as e:
            raise APIException(detail=f"An error ocurred while updating post analytics : {str(e)}")
        return self.response({
            "message":"click incremeted successfuly",
            "clicks":post_analytics.clicks             
        })

class CategoryListView(StandardAPIView):
    def get(self, request):

        try:
            # Parametros de solicitud
            parent_slug = request.query_params.get("parent_slug", None)
            ordering = request.query_params.get("ordering", None)
            sorting = request.query_params.get("sorting", None)
            search = request.query_params.get("search", "").strip()
            page = request.query_params.get("p", "1")

            # Construir clave de cache para resultados paginados
            cache_key = f"category_list:{page}:{ordering}:{sorting}:{search}:{parent_slug}"
            cached_categories = cache.get(cache_key)
            if cached_categories:
                # Serializar los datos del caché
                serialized_categories = CategoryListSerializer(cached_categories, many=True).data
                # Incrementar impresiones en Redis para los posts del caché
                for category in cached_categories:
                    redis_client.incr(f"category:impressions:{category.id}")  # Usar `post.id`
                return self.paginate(request, serialized_categories)

            # Consulta inicial optimizada
            if parent_slug:
                categories = Category.objects.filter(parent__slug=parent_slug).prefetch_related(
                    Prefetch("category_analytics", to_attr="analytics_cache")
                )
            else:
                # Si no especificamos un parent_slug buscamos las categorias padre
                categories = Category.objects.filter(parent__isnull=True).prefetch_related(
                    Prefetch("category_analytics", to_attr="analytics_cache")
                )

            if not categories.exists():
                raise NotFound(detail="No categories found.")
            
            # Filtrar por busqueda
            if search != "":
                categories = categories.filter(
                    Q(name__icontains=search) |
                    Q(slug__icontains=search) |
                    Q(title__icontains=search) |
                    Q(description__icontains=search)
                )
            
            # Ordenamiento
            if sorting:
                if sorting == 'newest':
                    categories = categories.order_by("-created_at")
                elif sorting == 'recently_updated':
                    categories = categories.order_by("-updated_at")
                elif sorting == 'most_viewed':
                    categories = categories.annotate(popularity=F("analytics_cache__views")).order_by("-popularity")

            if ordering:
                if ordering == 'az':
                    posts = posts.order_by("name")
                if ordering == 'za':
                    posts = posts.order_by("-name")

            # Guardar los objetos en el caché
            cache.set(cache_key, categories, timeout=60 * 5)

            # Serializacion
            serialized_categories = CategoryListSerializer(categories, many=True).data

            # Incrementar impresiones en Redis
            for category in categories:
                redis_client.incr(f"category:impressions:{category.id}")

            return self.paginate(request, serialized_categories)
        except Exception as e:
                raise APIException(detail=f"An unexpected error occurred: {str(e)}")
           
           
class CategoryDetailView(APIView):
    
    def get(self, request):

        try:
            # Obtener parametros
            slug = request.query_params.get("slug", None)
            page = request.query_params.get("p", "1")

            if not slug:
                return self.error("Missing slug parameter")
            
            # Construir cache
            cache_key = f"category_posts:{slug}:{page}"
            cached_posts = cache.get(cache_key)
            if cached_posts:
                # Serializar los datos del caché
                serialized_posts = PostListSerializer(cached_posts, many=True).data
                # Incrementar impresiones en Redis para los posts del caché
                for post in cached_posts:
                    redis_client.incr(f"post:impressions:{post.id}")  # Usar `post.id`
                return Response(serialized_posts)

            # Obtener la categoria por slug
            category = get_object_or_404(Category, slug=slug)

            # Obtener los posts que pertenecen a esta categoria
            posts = Post.postobjects.filter(category=category).select_related("category").prefetch_related(
                Prefetch("post_analytics", to_attr="analytics_cache")
            )
            
            if not posts.exists():
                raise NotFound(detail=f"No posts found for category '{category.name}'")
            
            # Guardar los objetos en el caché
            cache.set(cache_key, posts, timeout=60 * 5)

            # Serializar los posts
            serialized_posts = PostListSerializer(posts, many=True).data

            # Incrementar impresiones en Redis
            for post in posts:
                redis_client.incr(f"post:impressions:{post.id}")

            return Response( serialized_posts)
        except Exception as e:
            raise APIException(detail=f"An unexpected error occurred: {str(e)}")         
           
           
class ListPostCommentsView(StandardAPIView):
    def get(self,request):
        
        post_slug= request.query_params.get("slug",None)
        page=request.query_params.get("p","1")
        
        if not post_slug:
            raise NotFound(detail="A valid post slug must be provided")
        
        cache_key=f"post comments:{post_slug}:{page}"
        cached_comments=cache.get(cache_key)
        
        if cached_comments :
            return self.paginate(request,cached_comments)
        
        try:
            post=Post.objects.get(slug=post_slug)
        except Post.DoesNotExist:
            raise ValueError(f"Post:{post_slug} does not exist")
        
        comments = Comment.objects.filter(post=post,parent=None)
        
        serialized_comments=CommentSerializer(comments,many=True).data
        
        
        cache_index_key=f"post_comment_cache_key:{post_slug}"
        cache_keys=cache.get(cache_index_key,[])
        cache_keys.append(cache_key)
        cache.set(cache_index_key, cache_keys, timeout=60 * 5)
        
        cache.set(cache_keys,serialized_comments, timeout=60 * 5)
        
        return self.paginate(request,serialized_comments)   
    
                      
class IncrementCategoryClicksView(APIView):
    
    def post(self,request):
        
        
        data=request.data
        try:
            category=Category.objects.get(slug=data['slug'])
        except Category.DoesNotExist:
            raise NotFound(detail="the requested post does not exist")
             
        try:
            category_analytics, created = CategoryAnalytics.objects.get_or_create(category  =category)
            category_analytics.increment_clicks()  # Correcto: sin argumentos adicionales
        except Exception as e:
            raise APIException(detail=f"An error ocurred while updating post analytics : {str(e)}")
        return self.response({
            "message":"click incremeted successfuly",
            "clicks":category_analytics.clicks             
        })           
           
class PostCommentViews(StandardAPIView):
    permissions_classes=[permissions.IsAuthenticated]
     
    
    def post(self,request):
        
        
        
        post_slug=request.data.get("post_slug",None)
        user=request.user
        ip_address=get_client_ip(request)
        content=sanitize_html(request.data.get("content",None))
        
        
        
        if not post_slug:
            raise NotFound(detail="A valid post slug must be provided")
        
        try:
            post=Post.objects.get(slug=post_slug)
        
        except Post.DoesNotExist:
            raise ValueError(f"post:{post_slug} does not exist")
        
        comment=Comment.objects.create(
            user=user,
            post=post,
            content=content,
        )
        
        self._invalidate_post_comment_cache(post_slug)
        
        self._register_comment_interaction(comment,post,ip_address,user)
        
        return self.response(f"comment created for post:{post.title}")
    
    def put(self, request):
        comment_id = request.data.get("comment_id", None)
        user = request.user
        content = sanitize_html(request.data.get("content", None))

        if not comment_id:
            raise NotFound(detail="A valid comment id must be provided")

        try:
            comment = Comment.objects.get(id=comment_id, user=user)
        except Comment.DoesNotExist:
            raise ValueError(f"comment:{comment_id} does not exist")

        if not content:
            raise ValidationError(detail="Content is required")

        comment.content = content
        comment.save()

        self._invalidate_post_comment_cache(comment.post.slug)

        if comment.parent and comment.parent.replies.exists():
            self._invalidate_comment_replies_cache(comment.parent.id)

        return self.response("Comment updated successfully")   
    
    def delete(self, request):
        comment_id = request.query_params.get("comment_id", None)
        user = request.user

        if not comment_id:
            raise NotFound(detail="A valid comment id must be provided")

        comment = get_object_or_404(Comment, id=comment_id, user=user) #Usando get_object_or_404

        post = comment.post
        post_analytics, _ = PostAnalytics.objects.get_or_create(post=comment.post)

        if comment.parent and comment.parent.replies.exists():
            self._invalidate_comment_replies_cache(comment.parent.id)

        comment.delete()

        comments_count = Comment.objects.filter(post=post, is_active=True).count() #Corrige el error en el count.

        post_analytics.comments = comments_count
        post_analytics.save()

        self._invalidate_post_comment_cache(post.slug)

        return self.response("comment delete successful")

    def _register_comment_interaction(self,comment,post,ip_address,user):

        PostInteraccion.objects.create(
            user=user,
            post=post,
            interaction_type="comment",
            comment=comment,
            ip_address=ip_address
            
            )
    
        analytics, _ = PostAnalytics.objects.get_or_create(post=post)
        analytics.increment_metric("comments")   
    
    def _invalidate_post_comment_cache(self,post_slug):
        
        cache_index_key=f"post_comments_cache_key:{post_slug}"
        cache_keys=cache.get(cache_index_key,[])
        
        
        for key in cache_keys:
            cache.delete(key)
        
         
        cache.delete(cache_index_key)
        
        
    def _invalidate_comment_replies_cache(self, comment_id):
        
        
        cache_index_key=f"_invalidate_comment_replies_cache:{comment_id}"
        cache_keys=cache.get(cache_index_key,[])
        
        for key in cache_keys:
            cache.delete(key)
        
        cache.delete(cache_index_key)   
        
        
class ListCommentRepliesView(StandardAPIView):
    permissions_classes=[permissions.IsAuthenticated]
    def get(self,request):
        
        comment_id=request.query_params.get("comment_id",None)
        page=request.query_params.get("p","1")
        
        if not comment_id:
            raise NotFound(detail="A valid comment id must be provided")
        
        cache_key=f"comment replies:{comment_id}:{page}"
        cached_replies=cache.get(cache_key)
        if cached_replies :
            return self.paginate(request, cached_replies)
                
        
        
        
        try:
            parent_comment=Comment.objects.get(id=comment_id)
        except Comment.DoesNotExist:
            raise NotFound(f"comment:{comment_id} does not exist")
        
        
        replies=parent_comment.replies.filter(is_active=True).order_by("-created_at")
        
        
        serialized_replies=CommentSerializer(replies,many=True).data
        
        self._register_comment_reply_cache_key(comment_id,cache_key)
        
        cache.set(cache_key,serialized_replies, timeout=60 * 5)
        
        
        return self.paginate(request,serialized_replies,) 
        
    def _register_comment_reply_cache_key(self,comment_id,cache_key):
        
        
        cache_index_key=f"comment_replies_cache_keys:{comment_id}"
        cache_keys=cache.get(cache_index_key,[])
        if cache_key not in cache_keys:
            cache_keys.append(cache_key)
        cache.set(cache_index_key,cache_keys,timeout=60 * 5)
        
        
class CommentReplyViews(StandardAPIView):
    permissions_classes=[permissions.IsAuthenticated]
    
    def post(self,request):
        
        comment_id=request.data.get("comment_id",None)
        user=request.user
        ip_address=get_client_ip(request)
        content=sanitize_html(request.data.get("content",None))
        
        if not comment_id:
            raise NotFound(detail="A valid comment id must be provided")
        
        try:
            parent_comment=Comment.objects.get(id=comment_id)
        except Comment.DoesNotExist:
            raise ValueError(f"comment:{comment_id} does not exist")
        
        
        comment= Comment.objects.create(
            user=user,
            post=parent_comment.post,
            parent=parent_comment,
            content=content,
              
        )
        
        
        self._invalidate_post_replies_cache(comment_id)
        
        self._register_comment_interaction(comment,comment.post,ip_address,user)
        
        return self.response("comment created successfuly")

    def _register_comment_interaction(self,comment,post,ip_address,user):

        PostInteraccion.objects.create(
            user=user,
            post=post,
            interaction_type="comment",
            comment=comment,
            ip_address=ip_address
            
            )
    
        analytics, _ = PostAnalytics.objects.get_or_create(post=post)
        analytics.increment_metric("comments")
    
    def _invalidate_post_replies_cache(self,comment_id):
        
        cache_index_key=f"comment_replies_cache_keys:{comment_id}"
        cache_keys=cache.get(cache_index_key,[])
        
        
        for key in cache_keys:
            cache.delete(key)
        
         
        cache.delete(cache_index_key)
        
        
        
class PostLikeView(StandardAPIView):
    permissions_classes=[permissions.IsAuthenticated] 
    
    def post(self,request):
        
        post_slug=request.data.get("slug",None)
        user=request.user
        ip_address=get_client_ip(request)
        
        if not post_slug:
            raise NotFound(detail="A valid post slug must be provided")
        
        try:
            post=Post.objects.get(slug=post_slug)
        except Post.DoesNotExist:
            raise ValueError(f"post:{post_slug} does not exist")
        
        if PostLike.objects.filter(post=post,user=user).exists():
            
            raise ValidationError(detail="You have already liked this post")
        
        PostLike.objects.create(post=post,user=user)
        
        PostInteraccion.objects.create(
            user=user,
            post=post,
            interaction_type="like",
            ip_address=ip_address
        )
        
        analytics, _ = PostAnalytics.objects.get_or_create(post=post)
        analytics.increment_metric("likes")
        
        return self.response(f"you have a liked the post {post.title}")
    
    def delete(self,request):
        
        post_slug=request.query_params.get("slug",None)
        user=request.user

        if not post_slug:
            raise NotFound(detail="A valid post slug must be provided")
        
        try:
            post = Post.objects.get(slug=post_slug)
        except Post.DoesNotExist:
            raise ValueError(f"post with a slug:{post_slug} does not exist")
            
        try:
            like=PostLike.objects.get(post=post,user=user)
        except PostLike.DoesNotExist:
            raise ValidationError(detail="You have not liked this post")
        
        like.delete()
        
        
        analytics, _ = PostAnalytics.objects.get_or_create(post=post)
        analytics.likes=PostLike.objects.filter(post=post).count()
        analytics.save()
        
        return self.response(f"you have unliked the post {post.title}")
        
 
class PostShareView(StandardAPIView):
    permissions_classes=[permissions.IsAuthenticated]
    def post(self,request):
        
        
        post_slug=request.data.get("slug",None)
        plataform=request.data.get("plataform","other").lower()
        user= request.user if request.user.is_authenticated else None
        ip_address=get_client_ip(request)
        
        if not post_slug:
            raise NotFound(detail="A valid post slug must be provided")
        
        try:
            post= Post.objects.get(slug=post_slug)
        except Post.DoesNotExist:
            raise NotFound(detail=f"post:{post_slug} does not exist")
        
        valid_plataforms=[choice[0] for choice in PostShare._meta.get_field("plataform").choices]
        if plataform not in valid_plataforms:
            raise ValidationError(detail=f"invalid plataform. Valid options are {', '.join(valid_plataforms)}")
        
        PostShare.objects.create(
            post=post,
            user=user,
            plataform=plataform
            )

        PostInteraccion.objects.create(
            user=user,
            post=post,
            interaction_type="share",
            ip_address=ip_address
        )
        
        analytics, _ = PostAnalytics.objects.get_or_create(post=post)
        analytics.increment_metric("shares")
        
        
        
        return self.response(f"post '{post.title}' shared successfuly on {plataform.capitalize()}")
 
        
class GenerateFakePostView(StandardAPIView):
    
    def get(self,request):
        fake = Faker()
        
        categories = list(Category.objects.all())
        
        if not categories:
            return self.response("No categories found",400)
        
        posts_to_generate=100
        status_options = ["draft", "published"]
        
        for _ in range(posts_to_generate):
            title = fake.sentence(nb_words=6)
            user=UserAccount.objects.get(username="felipe1")
            post = Post(
                id=uuid.uuid4(),
                user=user,
                title = title,
                description= fake.sentence(nb_words=12),
                content=fake.paragraph(nb_sentences=5),
                keywords=", ".join(fake.words(nb=5)),
                slug = slugify(title),
                category=random.choice(categories),
                status=random.choice(status_options),
            )
            post.save()
            
        return self.response(f"{posts_to_generate} post generados correctamente")
    
class GenerateFakeAnalyticsView(StandardAPIView):
    
    def get(self,request):
        
        fake=Faker()
        
        
        posts = Post.objects.all()
        
        if not posts:
            return self.response({"error":"No posts found"},status=400)
        
        analytics_to_generate=len(posts)
        
        for post in posts:
            views=random.randint(50,1000)
            impressions = views + random.randint(100,2000)
            clicks=random.randint(0, views)
            avg_time_on_page=round(random.uniform(10,300),2)
            
            
            analytics, created=PostAnalytics.objects.get_or_create(post=post)
            analytics.views=views
            analytics.impressions = impressions
            analytics.clicks = clicks
            analytics.avg_time_on_page = avg_time_on_page
            analytics._update_click_through_rate()
            analytics.save()
            
        return self.response({"message":f"analiticas generadas para {analytics_to_generate} posts"}) 