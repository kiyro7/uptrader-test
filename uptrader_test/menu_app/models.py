from django.db import models
from django.urls import reverse, NoReverseMatch


class Menu(models.Model):
    """Меню — контейнер для пунктов"""
    name = models.CharField(max_length=100, unique=True, help_text='Internal name, used in template tag')
    title = models.CharField(max_length=200, blank=True, help_text='Title (human-readable)')

    class Meta:
        verbose_name = 'Menu'
        verbose_name_plural = 'Menus'

    def __str__(self):
        return self.title or self.name


class MenuItem(models.Model):
    """Пункт меню. Иерархия реализована через parent FK."""
    menu = models.ForeignKey(Menu, related_name='items', on_delete=models.CASCADE)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)

    # URL может быть либо явным (raw_url), либо именованным (named_url)
    raw_url = models.CharField(max_length=500, blank=True, help_text='Absolute or relative URL, e.g. "/about/" or "https://..."')
    named_url = models.CharField(max_length=200, blank=True, help_text='Django named URL (no args supported). Example: app:view_name')

    # порядок внутри уровня
    order = models.PositiveIntegerField(default=0)

    # дополнительные опции
    open_in_new_tab = models.BooleanField(default=False)

    class Meta:
        ordering = ['parent_id', 'order']
        verbose_name = 'Menu item'
        verbose_name_plural = 'Menu items'

    def __str__(self):
        return self.title

    def get_url(self):
        """
        Возвращает URL строки для ссылки. Для named_url пытается выполнить reverse(),
        если не получилось — вернёт raw_url. Если обе пустые — вернёт '#'.

        NOTE: named_url **без** аргументов. Если вам нужны args — можно расширить модель.
        """
        if self.named_url:
            try:
                return reverse(self.named_url)
            except NoReverseMatch:
                # fall back to raw_url if reverse fails
                pass
        if self.raw_url:
            return self.raw_url
        return '#'
