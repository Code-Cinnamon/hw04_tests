from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from ..models import Group, Post

User = get_user_model()


class PostFormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.TestUser = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title="Тестовая заголовок",
            slug='test-slug',
            description='Тестовое описание',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.TestUser)

    def test_authorized_client_post_create(self):
        """"Создается новый пост"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Данные из формы',
            'group': self.group.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        post = Post.objects.first()
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': post.author}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(post.text, form_data["text"])
        self.assertEqual(post.author, self.TestUser)
        self.assertEqual(post.group, PostFormsTests.group)

    def test_guest_client_post_create(self):
        """"Неавторизованный клиент не может создавать посты."""
        form_data = {
            'text': 'Пост от неавторизованного клиента',
            'group': self.group.id
        }
        post_count = Post.objects.count()
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        login_url = reverse('users:login')
        create_url = reverse('posts:post_create')
        self.assertRedirects(response, f'{login_url}?next={create_url}')
        self.assertEqual(post_count, Post.objects.count())

    def test_authorized_post_edit(self):
        """"Авторизованный клиент может редактировать посты."""
        post = Post.objects.create(
            text='Тестовый текст',
            author=self.TestUser,
            group=self.group,
        )
        form_data = {
            'text': 'Измененный текст',
            'group': self.group.pk,
        }
        posts_count = Post.objects.count()
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post.pk}),
            data=form_data,
            follow=True
        )
        redirect = reverse(
            'posts:post_detail',
            kwargs={'post_id': post.pk}
        )
        self.assertRedirects(response, redirect)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                text=form_data["text"],
                group=self.group.pk,
                author=self.TestUser
            ).exists()
        )
