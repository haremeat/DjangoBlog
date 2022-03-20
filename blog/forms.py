from .models import Comment


class CommentForm(Comment.ModelForm):
    class Meta:
        model = Comment,
        fields = ('content',)
        # 아래와 같은 형식으로 exclude로 쓸 수도 있다.
        # exclude = ('post', 'author', 'created_at')
