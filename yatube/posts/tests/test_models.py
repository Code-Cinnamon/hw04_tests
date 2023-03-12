from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_model_post_have_correct_object_names(self):
        """Проверяем, что у моделей Post корректно работает __str__."""
        post = PostModelTest.post
        correct_object_names = post.text[:15]
        self.assertEqual(correct_object_names, str(post))

    def test_model_group_have_correct_object_names(self):
        """Проверяем, что у моделей Group корректно работает __str__."""
        group = PostModelTest.group
        correct_object_names = group.title
        self.assertEqual(correct_object_names, str(group))
