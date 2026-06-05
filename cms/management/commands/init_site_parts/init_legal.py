from wagtail.models import Page

from cms.models import (
    ContactSettings,
    LegalDocumentPage,
    LegalIndexPage,
)
from cms.models.seo import SeoAbstract


def init_legal_pages(command, homepage):
    """
    Creates a 'Legal' parent page and nested legal documents.
    """
    command.stdout.write("Checking for Legal Pages...")

    contact_settings = ContactSettings.load()
    operator_name = contact_settings.legal_full_name or "Индивидуальный предприниматель"
    operator_address = contact_settings.legal_address or "[Юридический адрес]"
    operator_unp = contact_settings.legal_unp or "[УНП]"
    operator_email = contact_settings.email or "[Email]"

    # 1. Create Legal parent page if it doesn't exist
    legal_parent = LegalIndexPage.objects.descendant_of(homepage).filter(slug="legal").first()
    if not legal_parent:
        # Check if it exists but as a plain Page (from previous init)
        existing_plain = Page.objects.descendant_of(homepage).filter(slug="legal").first()
        if existing_plain:
            command.stdout.write("Deleting existing plain Legal page...")
            existing_plain.delete()

        command.stdout.write("Creating Legal parent page (LegalIndexPage)...")
        legal_parent = LegalIndexPage(
            title="Юридическая информация",
            slug="legal",
            body="<p>В данном разделе представлены основные юридические документы, регламентирующие работу нашего сервиса и правила обработки данных.</p>",
            meta_robots=SeoAbstract.MetaRobotsChoices.NOINDEX_NOFOLLOW,
            show_in_menus=False,
        )
        homepage.add_child(instance=legal_parent)
        legal_parent.save_revision().publish()
        command.stdout.write(command.style.SUCCESS("Legal parent page created."))
    else:
        # Update meta_robots if not set
        if legal_parent.meta_robots != SeoAbstract.MetaRobotsChoices.NOINDEX_NOFOLLOW:
            legal_parent.meta_robots = SeoAbstract.MetaRobotsChoices.NOINDEX_NOFOLLOW
            legal_parent.save_revision().publish()
            command.stdout.write(command.style.SUCCESS("Legal parent page SEO tags updated."))

    # 2. Create Privacy Policy
    privacy_policy = LegalDocumentPage.objects.descendant_of(legal_parent).filter(slug="privacy-policy").first()
    if not privacy_policy:
        # Check if it exists as old LegalPage
        existing_old = Page.objects.descendant_of(legal_parent).filter(slug="privacy-policy").first()
        if existing_old:
            existing_old.delete()

        command.stdout.write("Creating Privacy Policy page...")

        privacy_body = f"""
        <h2>ПОЛИТИКА В ОТНОШЕНИИ ОБРАБОТКИ ПЕРСОНАЛЬНЫХ ДАННЫХ</h2>
        <p><strong>1. ОБЩИЕ ПОЛОЖЕНИЯ</strong></p>
        <p>1.1. Настоящая Политика в отношении обработки персональных данных (далее – Политика) разработана во исполнение требований абз. 3 п. 3 ст. 17 Закона Республики Беларусь от 07.05.2021 № 99-З «О защите персональных данных» (далее – Закон) и действует в отношении всех персональных данных, которые {operator_name} (далее – Оператор) может получить от субъектов персональных данных.</p>
        <p>1.2. Юридический адрес Оператора: {operator_address}. УНП {operator_unp}.</p>
        <p>1.3. Политика применяется к персональным данным, собираемым Оператором через интернет-сайт (далее – Сайт), включая формы обратной связи и разделы для публикации отзывов.</p>
        <p>1.4. Целью настоящей Политики является обеспечение надлежащей защиты персональных данных от несанкционированного доступа и разглашения.</p>

        <p><strong>2. ЦЕЛИ И КАТЕГОРИИ ОБРАБАТЫВАЕМЫХ ДАННЫХ</strong></p>
        <p>2.1. Оператор осуществляет обработку персональных данных в следующих целях:</p>
        <ul>
            <li><strong>Обсуждение вопросов по оказанию услуг:</strong> обработка запросов, поступивших через формы обратной связи. Состав данных: имя, номер телефона, текст сообщения.</li>
            <li><strong>Публикация отзывов на Сайте:</strong> размещение отзывов пользователей для информирования других посетителей. Состав данных: имя (автор), текст отзыва, оценка.</li>
            <li><strong>Функционирование Сайта:</strong> использование технических файлов cookie для обеспечения безопасности (включая защиту от CSRF-атак) и корректной работы интерфейса (например, для сохранения темы оформления).</li>
        </ul>

        <p><strong>3. ПРАВОВЫЕ ОСНОВАНИЯ ОБРАБОТКИ</strong></p>
        <p>3.1. Обработка персональных данных осуществляется на основании согласия субъекта персональных данных, за исключением случаев, предусмотренных законодательством Республики Беларусь.</p>

        <p><strong>4. ПОРЯДОК И УСЛОВИЯ ОБРАБОТКИ</strong></p>
        <p>4.1. Обработка персональных данных ограничивается достижением конкретных, заранее определенных и законных целей.</p>
        <p>4.2. Хранение персональных данных осуществляется на сервере, расположенном на территории Республики Беларусь.</p>
        <p>4.3. Оператор не осуществляет трансграничную передачу персональных данных.</p>
        <p>4.4. Оператор принимает необходимые правовые, организационные и технические меры для защиты персональных данных.</p>
        <p>4.5. Срок хранения персональных данных, собранных для обсуждения вопросов оказания услуг, составляет 3 года с момента последнего взаимодействия. Данные, собранные для публикации отзывов, хранятся до момента удаления отзыва или прекращения деятельности Сайта.</p>

        <p><strong>5. ПРАВА СУБЪЕКТОВ ПЕРСОНАЛЬНЫХ ДАННЫХ</strong></p>
        <p>5.1. Субъект персональных данных имеет право:</p>
        <ul>
            <li>на отзыв своего согласия;</li>
            <li>на получение информации, касающейся обработки своих персональных данных;</li>
            <li>на изменение своих персональных данных;</li>
            <li>на получение информации о предоставлении своих персональных данных третьим лицам;</li>
            <li>требовать прекращения обработки персональных данных и (или) их удаления;</li>
            <li>на обжалование действий (бездействия) и решений Оператора, связанных с обработкой персональных данных.</li>
        </ul>
        <p>5.2. Для реализации указанных прав субъект направляет Оператору заявление в письменной форме или в виде электронного документа на адрес {operator_email}.</p>

        <p><strong>6. ЗАКЛЮЧИТЕЛЬНЫЕ ПОЛОЖЕНИЯ</strong></p>
        <p>6.1. Оператор имеет право по своему усмотрению изменять и (или) дополнять условия настоящей Политики без предварительного уведомления пользователей.</p>
        <p>6.2. Настоящая Политика вступает в силу с момента ее опубликования на Сайте.</p>
        """

        privacy_policy = LegalDocumentPage(
            title="Политика конфиденциальности",
            slug="privacy-policy",
            body=privacy_body,
            meta_robots=SeoAbstract.MetaRobotsChoices.NOINDEX_NOFOLLOW,
            show_in_menus=False,
        )
        legal_parent.add_child(instance=privacy_policy)
        privacy_policy.save_revision().publish()
        command.stdout.write(command.style.SUCCESS("Privacy Policy page created."))
    else:
        # Update meta_robots if not set
        if privacy_policy.meta_robots != SeoAbstract.MetaRobotsChoices.NOINDEX_NOFOLLOW:
            privacy_policy.meta_robots = SeoAbstract.MetaRobotsChoices.NOINDEX_NOFOLLOW
            privacy_policy.save_revision().publish()
            command.stdout.write(command.style.SUCCESS("Privacy Policy page SEO tags updated."))

    # 3. Create User Agreement
    user_agreement = LegalDocumentPage.objects.descendant_of(legal_parent).filter(slug="user-agreement").first()
    if not user_agreement:
        # Check if it exists as old LegalPage
        existing_old = Page.objects.descendant_of(legal_parent).filter(slug="user-agreement").first()
        if existing_old:
            existing_old.delete()

        command.stdout.write("Creating User Agreement page...")

        terms_body = f"""
        <h2>ПОЛЬЗОВАТЕЛЬСКОЕ СОГЛАШЕНИЕ</h2>
        <p><strong>1. ОБЩИЕ ПОЛОЖЕНИЯ</strong></p>
        <p>1.1. Настоящее Пользовательское соглашение (далее – Соглашение) определяет условия использования материалов и сервисов Сайта пользователями.</p>
        <p>1.2. Сайт создан в целях информирования об услугах, оказываемых {operator_name} (далее – Владелец сайта), и обеспечения взаимодействия с потенциальными клиентами.</p>
        <p>1.3. Использование материалов и сервисов Сайта регулируется нормами действующего законодательства Республики Беларусь.</p>

        <p><strong>2. ПРАВА И ОБЯЗАННОСТИ СТОРОН</strong></p>
        <p>2.1. Пользователь имеет право:</p>
        <ul>
            <li>знакомиться с информацией об услугах на Сайте;</li>
            <li>направлять запросы через формы обратной связи для уточнения деталей оказания услуг;</li>
            <li>оставлять отзывы о работе сервиса.</li>
        </ul>
        <p>2.2. Пользователь обязуется:</p>
        <ul>
            <li>не предпринимать действий, которые могут рассматриваться как нарушающие законодательство РБ или нормы международного права;</li>
            <li>не использовать Сайт для распространения спама или иной недостоверной информации;</li>
            <li>предоставлять достоверные контактные данные при заполнении форм.</li>
        </ul>
        <p>2.3. Владелец сайта имеет право:</p>
        <ul>
            <li>в любое время в одностороннем порядке изменять содержание Сайта;</li>
            <li>модерировать (редактировать или удалять) отзывы пользователей перед их публикацией;</li>
            <li>ограничивать доступ к Сайту в случае нарушения Пользователем условий Соглашения.</li>
        </ul>
        <p>2.4. Все исключительные права на материалы, размещенные на Сайте (тексты, фотографии, графические изображения), принадлежат Владельцу сайта. Копирование или использование материалов без активной гиперссылки на Сайт запрещено.</p>

        <p><strong>3. ПОРЯДОК ОСТАВЛЕНИЯ ОТЗЫВОВ</strong></p>
        <p>3.1. Оставляя отзыв на Сайте, Пользователь подтверждает свое согласие на его публикацию в открытом доступе.</p>
        <p>3.2. Владелец сайта вправе не публиковать отзывы, содержащие нецензурную лексику, оскорбления, рекламную информацию или не относящиеся к деятельности Владельца сайта.</p>

        <p><strong>4. ОГРАНИЧЕНИЕ ОТВЕТСТВЕННОСТИ</strong></p>
        <p>4.1. Вся информация на Сайте носит справочный характер и не является публичной офертой.</p>
        <p>4.2. Владелец сайта не несет ответственности за перебои в работе Сайта, вызванные техническими причинами или действиями третьих лиц.</p>

        <p><strong>5. ЗАКЛЮЧИТЕЛЬНЫЕ ПОЛОЖЕНИЯ</strong></p>
        <p>5.1. Все возможные споры, вытекающие из настоящего Соглашения или связанные с ним, подлежат разрешению в соответствии с действующим законодательством Республики Беларусь.</p>
        <p>5.2. Бездействие со стороны Владельца сайта в случае нарушения кем-либо из Пользователей положений Соглашения не лишает Владельца сайта права предпринять позже соответствующие действия в защиту своих интересов.</p>
        <p>5.3. Владелец сайта вправе в любое время в одностороннем порядке изменять условия настоящего Соглашения.</p>
        """

        user_agreement = LegalDocumentPage(
            title="Пользовательское соглашение",
            slug="user-agreement",
            body=terms_body,
            meta_robots=SeoAbstract.MetaRobotsChoices.NOINDEX_NOFOLLOW,
            show_in_menus=False,
        )
        legal_parent.add_child(instance=user_agreement)
        user_agreement.save_revision().publish()
        command.stdout.write(command.style.SUCCESS("User Agreement page created."))
    else:
        # Update meta_robots if not set
        if user_agreement.meta_robots != SeoAbstract.MetaRobotsChoices.NOINDEX_NOFOLLOW:
            user_agreement.meta_robots = SeoAbstract.MetaRobotsChoices.NOINDEX_NOFOLLOW
            user_agreement.save_revision().publish()
            command.stdout.write(command.style.SUCCESS("User Agreement page SEO tags updated."))

    # 4. Link in ContactSettings
    updated = False
    if not contact_settings.privacy_policy_page or contact_settings.privacy_policy_page.id != privacy_policy.id:
        contact_settings.privacy_policy_page = privacy_policy
        updated = True
    if not contact_settings.terms_of_service_page or contact_settings.terms_of_service_page.id != user_agreement.id:
        contact_settings.terms_of_service_page = user_agreement
        updated = True
    if not contact_settings.legal_index_page or contact_settings.legal_index_page.id != legal_parent.id:
        contact_settings.legal_index_page = legal_parent
        updated = True

    if updated:
        contact_settings.save()
        command.stdout.write(command.style.SUCCESS("Legal pages linked in Contact Settings."))
