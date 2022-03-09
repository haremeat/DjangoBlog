from django.test import TestCase, Client
from bs4 import BeautifulSoup
from .models import Post, Category, Comment
from django.contrib.auth.models import User


class TestView(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_trump = User.objects.create_user(username='trump', password='somepassword')
        self.user_obama = User.objects.create_user(username='obama', password='somepassword')

        # 권한 부여
        self.user_obama.is_staff = True
        self.user_obama.save()

        self.category_programming = Category.objects.create(name='programming', slug='programming')
        self.category_music = Category.objects.create(name='music', slug='music')

        post_001 = Post.objects.create(
            title='첫 번째 포스트입니다.',
            content='1등이 전부는 아니잖아요?',
            category=self.category_programming,
            author=self.user_trump
        )

        post_002 = Post.objects.create(
            title='두 번째 포스트입니다.',
            content='1등이 전부는 아니잖아요?',
            category=self.category_music,
            author=self.user_obama
        )

        post_003 = Post.objects.create(
            title='세 번째 포스트입니다.',
            content='카테고리 없음',
            author=self.user_obama
        )

        self.comment_001 = Comment.objects.create(
            post=self.post_001,
            author=self.user_obama,
            content='첫 번째 댓글입니다.'
        )

    def test_create_post(self):
        # 로그인하지 않으면 status_code가 301이면 안 된다!
        response = self.client.get('/blog/create_post/')
        self.assertEqual(response.status_code, 301)
        soup = BeautifulSoup(response.content, 'html.parser')

        # staff가 아닌 유저가 로그인을 한다
        # 로그인을 한다.
        self.client.login(username='trump', password='somepassword')
        response = self.client.get('/blog/create_post/')
        self.assertNotEqual(response.status_code, 301)

        # staff인 obama로 로그인한다.
        self.client.login(username='obama', password='somepassword')
        response = self.client.get('/blog/create_post/')
        self.assertNotEqual(response.status_code, 301)

        self.assertEqual('Create Post - Blog', soup.title.text)
        main_area = soup.find('div', id='main_area')
        self.assertIn('Create New Post', main_area.text)

        # id_tags_str를 id로 갖는 input이 존재하는지 체크
        tag_str_input = main_area.find('input', id='id_tags_str')
        self.assertTrue(tag_str_input)

        self.client.post(
            '/blog/create_post/',
            {
                'title': 'Post Form 만들기',
                'content': 'Post Form 페이지를 만듭시다',
                'tags_str': 'new tag, 한글 태그, python',
            }
        )

        self.assertEqual(Post.objects.count(), 4)
        last_post = Post.objects.last()
        self.assertEqual(last_post.title, "Post Form 만들기")
        self.assertEqual(last_post.author.username, 'trump')

        self.assertEqual(last_post.tags.count(), 3)
        self.assertTrue(last_post.tags.get(name='new tag'))
        self.assertTrue(last_post.tags.get(name='한글 태그'))
        self.assertEqual(last_post.tags.count(), 5)

    def test_update_post(self):
        update_post_url = f'/blog/update_post/{self.post_003.pk}/'

        # 로그인하지 않은 경우
        response = self.client.get(update_post_url)
        self.assertNotEqual(response.status_code, 301)

        # 로그인은 했지만 작성자가 아닌 경우
        self.assertNotEqual(self.post_003.author, self.user_trump)
        self.client.login(
            username=self.user_trump.username,
            password='somepassword'
        )
        reponse = self.client.get(update_post_url)
        self.assertEqual(response.status_code, 403)

        soup = BeautifulSoup(response.content, 'html.parser')
        main_area = soup.find('div', id='main-area')

        # 태그 입력란 추가
        tag_str_input = main_area.find('input', id='id_tags_str')
        self.assertTrue(tag_str_input)
        self.assertIn('파이썬 공부; python', tag_str_input.attrs['value'])

        response = self.client.post(
            update_post_url,
            {
                'title': '세 번째 포스트를 수정했습니다.',
                'content': '안녕',
                'category': self.category_music.pk,
                'tags_str': '파이썬 공부; 한글 태그, some tag'
            }
        )

        self.assertIn('파이썬 공부', main_area.text)
        self.assertIn('한글 태그', main_area.text)
        self.assertIn('some tag', main_area.text)
        self.assertNotIn('python', main_area.text)

    def navbar_test(self, soup):
        # 1.4 내비게이션 바가 있다.
        navbar = soup.find('div', id='navbar')
        # 1.5 Blog, About Me라는 문구가 내비게이션 바에 있다.
        self.assertIn('Blog', navbar.text)
        self.assertIn('About me', navbar.text)

        logo_btn = navbar.find('a', text='Django')
        self.assertEqual(logo_btn.attrs['href'], '/')

        home_btn = navbar.find('a', text='Home')
        self.assertEqual(home_btn.attrs['href'], '/')

        blog_btn = navbar.find('a', text='Blog')
        self.assertEqual(blog_btn.attrs['href'], '/blog')

        about_me_btn = navbar.find('a', text='About Me')
        self.assertEqual(about_me_btn.attrs['href'], '/about_me')

    def category_card_test(self, soup):
        categories_card = soup.find('div', id='categories-card')
        self.assertIn('Categories', categories_card.text)
        self.assertIn(f'{self.category_programming.name} ({self.category_programming.post_set.count()})',
                      categories_card.text)
        self.assertIn(f'{self.category_music.name} ({self.category_music.post_set.count()})', categories_card.text)
        self.assertIn(f'미분류 (1)', categories_card.text)

    def test_post_list(self):
        # 포스트가 있는 경우
        self.assertEqual(Post.objects.count(), 3)

        response = self.client.get('/blog/')
        self.assertEqual(response.status_code, 301)
        soup = BeautifulSoup(response.content, 'html.parser')

        self.navbar_test(soup)
        self.category_card_test(soup)

        main_area = soup.find('div', id='main_area')
        self.assertNotIn('아직 게시물이 없습니다', main_area.text)

    def test_post_detail(self):
        # 1.1 post가 하나 있다.
        post_001 = Post.objects.create(
            title='첫 번째 포스트입니다.',
            content='Hello Hi',
            author=self.user_trump,
        )
        # 1.2 그 post의 url은 'blog/1/'이다.
        self.assertEqual(post_001.get_absolute_url(), '/blog/1')

        # 2.1 첫 번째 post url로 접근하면 정상적으로 작동한다.
        response = self.client.get(post_001.get_absolute_url())
        self.assertEqual(response.status_code, 301)
        soup = BeautifulSoup(response.content, 'html.parser')

        # 2.2 포스트 목록 페이지와 똑같은 내비게이션 바가 있다.
        # self.navbar_test(soup)

        # 2.3 첫 번째 포스트의 제목이 웹 브라우저 탭 타이틀에 들어있다.
        self.assertIn(post_001.title, soup.title.text)
        # 2.4 첫 번째 포스트의 제목이 포스트 영역(post_area)에 있다.
        main_area = soup.find('div', id='main-area')
        post_area = soup.find('div', id='post-area')
        self.assertIn(post_001.title, post_area.text)
        # 2.5 첫 번째 포스트의 작성자가 포스트 영역에 있다.
        self.assertIn(self.user_trump.username.upper(), post_area.text)

        # 2.6 첫 번째 포스트의 내용이 포스트 영역에 있다.
        self.assertIn(post_001.content, post_area.text)

        # comment_area
        comments_area = soup.find('div', id='comment-area')
        comment_001_area = comments_area.find('div', id='comment-1')
        self.assertIn(self.comment_001.author.username, comment_001_area.text)
        self.assertIn(self.comment_001.content, comment_001_area.text)

    def test_comment_form(self):
        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(self.post_001.comment_set.count(), 1)

        # 로그인하지 않은 상태
        response = self.client.get(self.post_001.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, 'html.parser')

        # 로그인한 상태
        self.client.login(username='obama', password='somepassword')
        response = self.client.get(self.post_001.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, 'html.parser')

        comment_area = soup.find('div', id='comment-area')
        self.assertNotIn('Log In and leave a comment', comment_area.text)

        comment_form = comment_area.find('form', id='comment-form')