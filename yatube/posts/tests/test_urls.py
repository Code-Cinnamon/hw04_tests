from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from http import HTTPStatus

from ..models import Post, Group

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.user = User.objects.create_user(username='test-author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост достаточной длины',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.non_author = User.objects.create_user(username='test-author')
        self.non_author_client = Client()
        self.non_author_client.force_login(self.user)

    def test_url_exists_at_desired_location(self):
        """Страница / доступна любому пользователю."""
        url_names = {
            '/',
            '/group/test-slug/',
            '/profile/test-author/',
            '/posts/1/',
        }
        for address in url_names:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response, HTTPStatus.OK)

    def test_create_url_exists_at_desired_location(self):
        """Страница /create/ доступна авторизованному пользователю."""
        url_names = {
            '/create_post/',
            '/posts/1/edit/',
        }
        for address in url_names:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response, HTTPStatus.OK)

    def test_unexisting_page(self):
        """Несуществующая страница"""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response, HTTPStatus.NOT_FOUND)

    def test_redirect_unonymos(self):
        """Страницы /create_post/ /post/1/edit/ /post/1/comment/
        перенаправляю анонимного пользователя на страницу логина"""
        url_names = {
            '/create_post/',
            '/posts/1/edit/',
            '/post/1/comment',
        }
        for address in url_names:
            with self.subTest(address=address):
                response = self.guest_client.get(address, follow=True)
                self.assertRedirects(response, '/auth/login/?next=')

    def test_post_edit_url_redirect_non_author_authorized(self):
        """Страница /posts/1/edit/ перенаправляет авторизованного пользователя,
        не являющегося автором поста на страницу /posts/1/"""
        response = self.non_author_client.get('/posts/1/edit/', follow=True)
        self.assertRedirects(response, '/posts/1/')

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        url_names = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/test-author/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/posts/1/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
            '/unexisting_page/': 'core/404.html',
        }
        for template, address in url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
