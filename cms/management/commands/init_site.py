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
    help = 'Initializes the site: configures HomePage, Site object, superuser and global settings based on .env'

    def add_arguments(self, parser):
        parser.add_argument(
            '--admin-only',
            action='store_true',
            help='Only create superuser',
        )
        parser.add_argument(
            '--content-only',
            action='store_true',
            help='Only create content (HomePage and Site)',
        )
        parser.add_argument(
            '--settings-only',
            action='store_true',
            help='Only initialize global settings (SocialMedia and Contact)',
        )

    def handle(self, *args, **options):
        load_dotenv()
        
        admin_only = options['admin_only']
        content_only = options['content_only']
        settings_only = options['settings_only']
        
        # If no flags are provided, run everything
        run_all = not (admin_only or content_only or settings_only)
        
        if run_all or admin_only:
            self.init_superuser()
            
        if run_all or settings_only:
            self.init_global_settings()
            
        if run_all or content_only:
            self.init_content()

        self.stdout.write(self.style.SUCCESS('Site initialization finished!'))

    def init_superuser(self):
        username = os.getenv('SUPERUSER_USERNAME')
        email = os.getenv('SUPERUSER_EMAIL')
        password = os.getenv('SUPERUSER_PASSWORD')

        if username and password:
            if not User.objects.filter(username=username).exists():
                self.stdout.write(f"Creating superuser {username}...")
                User.objects.create_superuser(username=username, email=email, password=password)
                self.stdout.write(self.style.SUCCESS(f"Superuser {username} created!"))
            else:
                self.stdout.write(self.style.WARNING(f"Superuser {username} already exists."))
        else:
            self.stdout.write(self.style.WARNING("SUPERUSER_USERNAME or SUPERUSER_PASSWORD not found in .env"))

    def init_global_settings(self):
        self.stdout.write("Initializing global settings (social and contacts)...")
        
        # Social Media Settings
        social_settings = SocialMediaSettings.load()
        if not any([social_settings.facebook, social_settings.instagram, social_settings.telegram]):
            social_settings.telegram = "https://t.me/homeservice"
            social_settings.whatsapp = "https://wa.me/79001234567"
            social_settings.instagram = "https://instagram.com/homeservice"
            social_settings.save()
            self.stdout.write(self.style.SUCCESS("Social media settings created."))
        else:
            self.stdout.write(self.style.WARNING("Social media settings already exist."))

        # Contact Settings
        contact_settings = ContactSettings.load()
        if not contact_settings.phone_number:
            contact_settings.phone_number = "+7 (900) 123-45-67"
            contact_settings.email = "info@homeservice.ru"
            contact_settings.address = "г. Москва, ул. Примерная, д. 1"
            contact_settings.save()
            self.stdout.write(self.style.SUCCESS("Contact settings created."))
        else:
            self.stdout.write(self.style.WARNING("Contact settings already exist."))

    def init_content(self):
        # 1. Site configuration from env
        site_url_env = os.getenv('SITE_URL', 'http://localhost:8000')
        parsed_url = urlparse(site_url_env)
        hostname = parsed_url.hostname or 'localhost'
        port = parsed_url.port
        if not port:
            port = 443 if parsed_url.scheme == 'https' else 80
            
        self.stdout.write(f"Configuring site for: {hostname}:{port} (from {site_url_env})")

        # 2. Find or create HomePage
        homepage = HomePage.objects.first()
        if not homepage:
            self.stdout.write("HomePage not found, creating...")
            root_page = Page.objects.get(id=1)
            # Remove default "Home" page if it exists
            Page.objects.filter(slug='home').delete()
            
            homepage = HomePage(
                title="Главная",
                slug='home',
                live=True,
            )
            root_page.add_child(instance=homepage)
            homepage.save_revision().publish()
            self.stdout.write(self.style.SUCCESS("HomePage created."))
        else:
            self.stdout.write(self.style.WARNING("HomePage already exists."))

        # 3. Fill with demo content if body is empty
        if not homepage.body:
            self.stdout.write("Filling HomePage with demo content...")
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
            self.stdout.write(self.style.SUCCESS("Demo content added to HomePage."))
        else:
            self.stdout.write(self.style.WARNING("HomePage body is not empty, skipping demo content."))

        # 4. Configure Site object
        site = Site.objects.filter(is_default_site=True).first() or Site.objects.first()
        
        if site:
            # Check if we need to update
            if site.hostname != hostname or site.port != port or site.root_page != homepage:
                self.stdout.write(f"Updating existing site: {site.hostname}:{site.port}")
                site.hostname = hostname
                site.port = port
                site.root_page = homepage
                site.save()
                self.stdout.write(self.style.SUCCESS("Site updated."))
            else:
                self.stdout.write(self.style.WARNING(f"Site {site.hostname}:{site.port} already correctly configured."))
        else:
            self.stdout.write("Creating new Site object...")
            Site.objects.create(
                hostname=hostname,
                port=port,
                root_page=homepage,
                is_default_site=True,
                site_name='HomeService'
            )
            self.stdout.write(self.style.SUCCESS("Site object created."))
