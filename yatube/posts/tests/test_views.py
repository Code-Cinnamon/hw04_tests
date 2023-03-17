from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
'''from django import forms'''
from django.urls import reverse

from ..forms import PostForm
from ..models import Post, Group, User

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title="Тестовый заголовок",
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
        )
        cls.index_url = ('posts:index', 'posts/index.html', None)
        cls.profile_url = (
            'posts:profile',
            'posts/profile.html',
            [cls.post.author]
        )
        cls.post_detail_url = (
            'posts:post_detail',
            'posts/post_detail.html',
            [cls.group.pk]
        )
        cls.edit_post_url = (
            'posts:post_edit',
            'posts/create_post.html',
            cls.post.pk
        )
        cls.new_post_url = (
            'posts:post_create',
            'posts/create_post.html'
        )
        cls.group_url = (
            'posts:group_posts',
            'posts/group_list.html',
            cls.group.slug
        )

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованный клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон и HTTP статус."""
        templates_page_names = {
            reverse('posts:group_list', kwargs={'slug': self.group.slug}): (
                'posts/group_list.html'
            ),
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:profile', kwargs={'username': (
                self.user.username)}): 'posts/profile.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_detail', kwargs={'post_id': (
                self.post.pk)}): 'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': (
                self.post.pk)}): 'posts/create_post.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def check_context_contains_page_or_post(self, context, post=False):
        if post:
            self.assertIn('post', context)
            post = context['post']
        else:
            self.assertIn('page_obj', context)
            post = context['page_obj'][0]
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.pub_date, self.post.pub_date)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group, self.post.group)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}))
        self.assertIn('group', response.context)
        group = response.context['group']
        self.assertEqual(group.title, self.group.title)
        self.assertEqual(group.description, self.group.description)

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        '''url, _, args = self.post_detail_url
        response = self.guest_client.get(reverse(url, args=args))
        self.assertTemplateUsed(response, _)'''
        response = self.guest_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id}))
        self.check_context_contains_page_or_post(response.context, post=True)
        self.assertIn('author', response.context)
        self.assertEqual(response.context['author'], self.user)
        self.assertIn('posts_count', response.context)
        self.assertEqual(
            response.context['posts_count'], self.user.posts.count()
        )

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        url, _, args = self.index_url
        response = self.guest_client.get(reverse(url, args=args))
        self.check_context_contains_page_or_post(response.context)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        url, _, args = self.profile_url
        response = self.guest_client.get(reverse(url, args=args))
        self.check_context_contains_page_or_post(response.context)

    def test_create_post_show_correct_context(self):
        """Шаблоны create и edit сформированы с правильным контекстом."""
        urls = (
            ("post_create", 'posts:post_create', None),
            ("post_edit", 'posts:post_edit', [self.post.pk])
        )
        for name, _, args in urls:
            with self.subTest(name=name):
                is_edit_value = bool(name == 'post_edit')
                response = self.authorized_client.get(reverse(_, args=args))
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], PostForm)
                self.assertIn('is_edit', response.context)
                is_edit = response.context['is_edit']
                self.assertIsInstance(is_edit, bool)
                self.assertEqual(is_edit, is_edit_value)

    def test_post_another_group(self):
        """Пост не попал в другую группу"""
        response = self.authorized_client.get(
            reverse('posts:group_list', args={self.group.slug}))
        first_object = response.context["page_obj"][0]
        post_text = first_object.text
        self.assertTrue(post_text, 'Тестовый текст')


class PostPaginatorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        Post.objects.bulk_create(
            [Post(author=cls.user, text=f"Тестовый пост {i}", group=cls.group)
                for i in range(13)]
        )

    def setUp(self):
        self.guest = Client()
        self.authorized = Client()
        self.authorized.force_login(self.user)

    def test_paginator(self):
        pages = (
                (1, 10),
                (2, 3)
        )

        urls = (
            reverse('posts:index', None),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user})
        )

        for url in urls:
            for page, count in pages:
                # заметь как передается квери параметр
                response = self.client.get(url, {"page": page})
                self.assertEqual(
                    len(response.context['page_obj']), count,
                )
