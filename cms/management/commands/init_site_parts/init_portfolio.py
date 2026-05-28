from cms.models import PortfolioIndexPage, NavigationSettings, MenuItem
from cms.models.seo import SeoAbstract


def init_portfolio_pages(command, homepage):
    """
    Initializes PortfolioIndexPage (Our Works).
    """
    # 1. Create PortfolioIndexPage if it doesn't exist
    portfolio_index = PortfolioIndexPage.objects.first()
    if not portfolio_index:
        command.stdout.write("PortfolioIndexPage (Наши работы) not found, creating...")
        portfolio_index = PortfolioIndexPage(
            title="Наши работы",
            slug="portfolio",
            body="Примеры наших выполненных работ.",
            seo_title="Наши работы - примеры мойки и покраски - HomeCleanService",
            search_description="Посмотрите примеры наших работ по мойке и покраске крыш, фасадов и заборов по всей Беларуси. Фото до и после, описание процесса.",
            og_type=SeoAbstract.OgTypeChoices.WEBSITE,
            meta_robots=SeoAbstract.MetaRobotsChoices.INDEX_FOLLOW,
            live=True,
            show_in_menus=True,
        )
        homepage.add_child(instance=portfolio_index)
        portfolio_index.save_revision().publish()
        command.stdout.write(
            command.style.SUCCESS("PortfolioIndexPage 'Наши работы' created.")
        )
    else:
        command.stdout.write(
            command.style.WARNING("PortfolioIndexPage already exists.")
        )
        if (
            portfolio_index.title != "Наши работы"
            or portfolio_index.slug != "portfolio"
        ):
            portfolio_index.title = "Наши работы"
            portfolio_index.slug = "portfolio"
            portfolio_index.save_revision().publish()
            command.stdout.write(
                command.style.SUCCESS(
                    "PortfolioIndexPage updated to 'Наши работы' with slug 'portfolio'."
                )
            )

    # 2. Add to Navigation Menu if not already there
    nav_settings = NavigationSettings.load()
    if not MenuItem.objects.filter(
        setting=nav_settings, link_page=portfolio_index
    ).exists():
        max_order = MenuItem.objects.filter(setting=nav_settings).count()
        MenuItem.objects.create(
            setting=nav_settings,
            label="Портфолио",
            link_page=portfolio_index,
            sort_order=max_order,
        )
        command.stdout.write(
            command.style.SUCCESS("Portfolio added to navigation menu.")
        )

    return portfolio_index
