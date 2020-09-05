from django.forms import ModelForm, Textarea, ValidationError
from django.utils.translation import gettext_lazy as _

from .models import Comment, Post


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ['group', 'text', 'image']
        help_texts = {
            'group': _('Группа, в которой будет размещена эта запись'),
            'text': _('Введите хотя бы один символ'),
            'image': _('Вы можете загрузить изображение для своего поста'),
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        help_texts = {
            'text': _('Введите свой комментарий'),
        }
        widgets = {
            'text': Textarea(attrs={'rows': 3}),
        }
