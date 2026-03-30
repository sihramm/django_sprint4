from django.db import models
from django.contrib.auth import get_user_model

class BaseModel(models.Model):
    is_published = models.BooleanField('Опубликовано', default=True)
    created_at = models.DateTimeField('Добавлено', auto_now_add=True)

    class Meta:
        abstract = True

User = get_user_model()


class Category(BaseModel):
    title = models.CharField('Заголовок', max_length=256)
    description = models.TextField('Описание')
    slug = models.SlugField('Идентификатор', unique=True)


    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.title


class Location(BaseModel):
    name = models.CharField('Название', max_length=256)


    class Meta:
        verbose_name = 'местоположение'
        verbose_name_plural = 'Местоположения'

    def __str__(self):
        return self.name


class Post(BaseModel):
    title = models.CharField('Заголовок', max_length=256)
    text = models.TextField('Текст')
    pub_date = models.DateTimeField('Дата и время публикации', help_text='...')
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Автор', related_name='posts')
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Местоположение')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, verbose_name='Категория')
    image = models.ImageField('Изображение', upload_to='posts/', blank=True, null=True)
    # is_published и created_at убрать

    class Meta:
        verbose_name = 'публикация'
        verbose_name_plural = 'Публикации'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, verbose_name='Публикация', related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Автор')
    text = models.TextField('Текст комментария')
    created_at = models.DateTimeField('Добавлено', auto_now_add=True)

    class Meta:
        ordering = ('created_at',)
        verbose_name = 'комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return self.text[:20]