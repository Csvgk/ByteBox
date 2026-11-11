from django.conf import settings
from django.db import models
from django.templatetags.static import static
from django.urls import reverse

from .utils import make_slug


class Category(models.Model):
    name = models.CharField('Назва', max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Рубрика'
        verbose_name_plural = 'Рубрики'

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField('Назва', max_length=40, unique=True)
    slug = models.SlugField(max_length=40, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class PublishedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_published=True)


class Post(models.Model):
    title = models.CharField('Заголовок', max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    excerpt = models.CharField('Короткий опис', max_length=300, help_text='Показується в списку статей')
    content = models.TextField('Текст статті')
    image = models.ImageField('Обкладинка', upload_to='blog/', blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='posts', verbose_name='Рубрика')
    tags = models.ManyToManyField(Tag, blank=True, related_name='posts', verbose_name='Теги')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='blog_posts',
                               verbose_name='Автор')
    is_published = models.BooleanField('Опубліковано', default=True)
    created_at = models.DateTimeField('Створено', auto_now_add=True)
    updated_at = models.DateTimeField('Оновлено', auto_now=True)

    objects = models.Manager()
    published = PublishedManager()

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Стаття'
        verbose_name_plural = 'Статті'

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = make_slug(self.title) or 'post'
            slug, n = base, 2
            while Post.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{n}'
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog:post_detail', args=[self.slug])

    @property
    def image_url(self):
        return self.image.url if self.image else static('img/blog-cover.svg')


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments', verbose_name='Стаття')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='blog_comments',
                               verbose_name='Автор')
    text = models.TextField('Коментар', max_length=2000)
    created_at = models.DateTimeField('Дата', auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Коментар'
        verbose_name_plural = 'Коментарі'

    def __str__(self):
        return f'{self.author}: {self.text[:40]}'
