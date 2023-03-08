from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from ..models import Group, Post

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test-author')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

    def test_pages_uses_correct_template(self):
        """Во view-функциях используются соответствующие шаблоны."""
        pages_names_templates = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}): (
                'posts/group_list.html'
            ),
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}): (
                'posts/profile.html'
            ),
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}): (
                'posts/post_detail.html'
            ),
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}): (
                'posts/create_post.html'
            ),
        }
        for reverse_name, template in pages_names_templates.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        """Шаблон страницы index сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:index')
        )
        for i in range(Post.objects.count()):
            self.assertEqual(
                response.context['page_obj'][i],
                Post.objects.get(pk=Post.objects.count() - i)
            )
        self.assertEqual(
            self.post.image,
            response.context['page_obj'][Post.objects.count() - 1].image,
        )

    def test_group_list_show_correct_context(self):
        """Шаблон страницы group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        for i in range(Post.objects.count()):
            self.assertEqual(
                response.context['page_obj'][i],
                Post.objects.get(pk=Post.objects.count() - i)
            )
        self.assertEqual(
            response.context['group'], self.group
        )
        self.assertEqual(
            self.post.image,
            response.context['page_obj'][Post.objects.count() - 1].image,
        )

    def test_profile_show_correct_context(self):
        """Шаблон страницы profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        for i in range(Post.objects.count()):
            self.assertEqual(
                response.context['page_obj'][i],
                Post.objects.get(pk=Post.objects.count() - i)
            )
        self.assertEqual(
            response.context['author'], self.user
        )
        self.assertEqual(
            response.context['post_number'],
            Post.objects.filter(author=self.user).count()
        )
        self.assertEqual(
            self.post.image,
            response.context['page_obj'][Post.objects.count() - 1].image,
        )

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        self.assertEqual(
            response.context['post'].text, self.post.text
        )
        self.assertEqual(
            response.context['post'].author, self.post.author
        )
        self.assertEqual(
            response.context['post'].group, self.post.group
        )
        self.assertEqual(
            response.context['post_number'],
            Post.objects.filter(author=self.user).count()
        )
        self.assertEqual(
            response.context['post'].image,
            self.post.image
        )

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_pages_with_pagination_contain_ten_and_four_records(self):
        """Шаблоны страниц index, group_list, profile сформированы
        с правильным количеством записей."""
        pages_names = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username}),
        ]
        for reverse_name in pages_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(
                    len(response.context['page_obj']), settings.POSTS_NUMBER
                )
                response = self.authorized_client.get(reverse_name + '?page=2')
                self.assertEqual(
                    len(response.context['page_obj']),
                    Post.objects.count() - settings.POSTS_NUMBER
                )
