from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from wagtail.models import Site, Page
from home.models import HomePage
from cms.models import SocialMediaSettings, ContactSettings
import json
import os
from urllib.parse import urlparse
from dotenv import load_dotenv

class Command(BaseCommand):
    help = 'Инициализирует сайт: настраивает HomePage, объект Site, суперпользователя и глобальные настройки на основе .env'

    def handle(self, *args, **options):
        # 0. Загружаем переменные из .env
        load_dotenv()
        
        # 0.1 Создание суперпользователя
        username = os.getenv('SUPERUSER_USERNAME')
        email = os.getenv('SUPERUSER_EMAIL')
        password = os.getenv('SUPERUSER_PASSWORD')

        if username and password:
            if not User.objects.filter(username=username).exists():
                self.stdout.write(f"Создание суперпользователя {username}...")
                User.objects.create_superuser(username=username, email=email, password=password)
                self.stdout.write(self.style.SUCCESS(f"Суперпользователь {username} создан!"))
            else:
                self.stdout.write(f"Суперпользователь {username} уже существует.")
        
        # 0.2 Инициализация глобальных настроек
        self.stdout.write("Инициализация глобальных настроек (соцсети и контакты)...")
        social_settings = SocialMediaSettings.load()
        if not any([social_settings.facebook, social_settings.instagram, social_settings.telegram]):
            social_settings.telegram = "https://t.me/homeservice"
            social_settings.whatsapp = "https://wa.me/79001234567"
            social_settings.instagram = "https://instagram.com/homeservice"
            social_settings.save()
            self.stdout.write(self.style.SUCCESS("Настройки соцсетей созданы."))

        contact_settings = ContactSettings.load()
        if not contact_settings.phone_number:
            contact_settings.phone_number = "+7 (900) 123-45-67"
            contact_settings.email = "info@homeservice.ru"
            contact_settings.address = "г. Москва, ул. Примерная, д. 1"
            contact_settings.save()
            self.stdout.write(self.style.SUCCESS("Контактные данные созданы."))

        # Читаем SITE_URL, по умолчанию используем localhost:8000
        site_url_env = os.getenv('SITE_URL', 'http://localhost:8000')
        parsed_url = urlparse(site_url_env)
        
        hostname = parsed_url.hostname or 'localhost'
        # Если порт не указан в URL, Django/Wagtail по умолчанию используют 80 (для http) или 443 (для https)
        # Но для разработки мы часто используем 8000
        port = parsed_url.port
        if not port:
            port = 443 if parsed_url.scheme == 'https' else 80
            
        self.stdout.write(f"Настройка сайта для: {hostname}:{port} (из {site_url_env})")

        # 1. Находим или создаем HomePage
        # По умолчанию Wagtail создает "Home" страницу с id=2 (после Welcome)
        # Но мы ищем именно нашу модель HomePage
        homepage = HomePage.objects.first()
        
        if not homepage:
            self.stdout.write("HomePage не найден, создаем...")
            # Пытаемся найти корневую страницу (обычно id=1)
            root_page = Page.objects.get(id=1)
            
            # Удаляем стандартную страницу "Home" если она есть, чтобы не мешалась
            Page.objects.filter(slug='home').delete()
            
            homepage = HomePage(
                title="Главная",
                slug='home',
                live=True,
            )
            root_page.add_child(instance=homepage)
            homepage.save_revision().publish()

        # 2. Наполняем контентом, если body пустой
        if not homepage.body:
            self.stdout.write("Наполняем HomePage демо-контентом...")
            homepage.body = [
                ('hero', {
                    'title': 'Профессиональная отмывка и покраска домов',
                    'subtitle': 'Вернем вашему дому первозданный вид за 2 дня. Чистка крыш, фасадов и мощение.',
                    'cta_text': 'Рассчитать стоимость',
                }),
                ('services', {
                    'title': 'Наши основные услуги',
                    'items': [
                        {
                            'name': 'Мойка высокого давления',
                            'description': 'Бережная очистка любых поверхностей от мха, грязи и высолов.'
                        },
                        {
                            'name': 'Покраска фасадов',
                            'description': 'Профессиональное окрашивание с гарантией на материалы и работу.'
                        },
                        {
                            'name': 'Чистка крыш',
                            'description': 'Удаление мха и лишайника, обработка защитными составами.'
                        }
                    ]
                })
            ]
            homepage.save_revision().publish()

        # 3. Настраиваем объект Site
        # Пытаемся найти существующий сайт на порту 80 или localhost
        site = Site.objects.filter(is_default_site=True).first() or Site.objects.first()
        
        if site:
            self.stdout.write(f"Обновляем существующий сайт: {site.hostname}:{site.port}")
            site.hostname = hostname
            site.port = port
            site.root_page = homepage
            site.save()
        else:
            self.stdout.write("Создаем новый объект Site...")
            Site.objects.create(
                hostname=hostname,
                port=port,
                root_page=homepage,
                is_default_site=True,
                site_name='HomeService'
            )

        self.stdout.write(self.style.SUCCESS('Сайт успешно инициализирован!'))
