from django import template
# В template.Library зарегистрированы все теги и фильтры шаблонов
# добавляем к ним и наш фильтр
register = template.Library()


@register.filter 
def addclass(field, css):
        return field.as_widget(attrs={"class": css})

# синтаксис @register... , под которой описан класс addclass() - 
# это применение "декораторов", функций, обрабатывающих функции
# мы скоро про них расскажем. Не бойтесь соб@к

@register.filter
def comments_numb(value):
    remainder = value % 10 
    if value == 0: 
        return 'нет комментариев' 
    elif remainder == 0 or remainder >= 5 or (10 <= value <= 19): 
        return f'{value} комментариев' 
    elif remainder == 1: 
        return f'{value} комментарий' 
    else: 
        return f'{value} комментария'