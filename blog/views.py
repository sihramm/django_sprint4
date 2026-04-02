from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Count
from django.conf import settings
from django.utils import timezone
from .models import Post, Comment, Category, Location
from .forms import PostForm, CommentForm, ProfileForm

User = get_user_model()

def get_filtered_posts():
    """Возвращает queryset опубликованных постов с аннотацией количества комментариев."""
    return Post.objects.filter(
        is_published=True,
        category__is_published=True,
        pub_date__lte=timezone.now()
    ).select_related(
        'author', 'category', 'location'
    ).annotate(
        comment_count=Count('comments')
    )

def get_paginated_page(queryset, request):
    """Возвращает объект пагинации для переданного queryset."""
    paginator = Paginator(queryset, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)

def index(request):
    post_list = get_filtered_posts().order_by('-pub_date')
    page_obj = get_paginated_page(post_list, request)
    return render(request, 'blog/index.html', {'page_obj': page_obj})

def category_posts(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug, is_published=True)
    post_list = get_filtered_posts().filter(category=category).order_by('-pub_date')
    page_obj = get_paginated_page(post_list, request)
    return render(request, 'blog/category.html', {
        'page_obj': page_obj,
        'category': category
    })

def profile(request, username):
    author = get_object_or_404(User, username=username)
    # Базовый queryset для постов автора
    if request.user == author:
        # Автор видит все свои посты (включая отложенные и снятые с публикации)
        post_list = Post.objects.filter(author=author).select_related(
            'category', 'location'
        ).annotate(
            comment_count=Count('comments')
        ).order_by('-pub_date')
    else:
        # Чужие пользователи видят только опубликованные посты
        post_list = get_filtered_posts().filter(author=author).order_by('-pub_date')
    page_obj = get_paginated_page(post_list, request)
    return render(request, 'blog/profile.html', {
        'page_obj': page_obj,
        'author': author,
    })

def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    # Проверка доступности поста для неавтора
    if not post.is_published or not post.category.is_published or post.pub_date > timezone.now():
        if request.user != post.author:
            return redirect('blog:index')
    comments = post.comments.select_related('author').all()
    form = CommentForm()
    return render(request, 'blog/detail.html', {
        'post': post,
        'comments': comments,
        'form': form,
    })

@login_required
def post_create(request):
    form = PostForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('blog:profile', username=request.user.username)
    return render(request, 'blog/create.html', {'form': form})

@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)
    form = PostForm(request.POST or None, request.FILES or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id=post_id)
    return render(request, 'blog/create.html', {'form': form, 'post': post})

@login_required
def post_delete(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)
    if request.method == 'POST':
        post.delete()
        return redirect('blog:profile', username=request.user.username)
    return render(request, 'blog/create.html', {'post': post, 'delete_mode': True})

@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
    return redirect('blog:post_detail', post_id=post_id)

@login_required
def edit_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, post_id=post_id)
    if comment.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)
    form = CommentForm(request.POST or None, instance=comment)
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id=post_id)
    return render(request, 'blog/comment.html', {'form': form, 'comment': comment})

@login_required
def delete_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, post_id=post_id)
    if comment.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)
    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', post_id=post_id)
    return render(request, 'blog/comment.html', {'comment': comment, 'delete_mode': True})

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('blog:profile', username=request.user.username)
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'blog/edit_profile.html', {'form': form})