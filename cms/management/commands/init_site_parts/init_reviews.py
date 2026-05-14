from cms.models import Review


def init_reviews(command):
    command.stdout.write("Checking for demo reviews...")
    if not Review.objects.exists():
        Review.objects.create(
            author="Александр Е.",
            text="Заказывал мойку и покраску крыши. Ребята приехали вовремя, сделали всё очень аккуратно. Крыша выглядит как новая! Рекомендую.",
            rating=5,
            is_approved=True,
            ip="127.0.0.1",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        Review.objects.create(
            author="Мария С.",
            text="Очень довольна результатом очистки фасада. Все пятна ушли, дом преобразился. Спасибо за профессионализм!",
            rating=5,
            is_approved=True,
            ip="127.0.0.1",
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        Review.objects.create(
            author="Иван Петрович",
            text="Хорошая работа. Быстро, четко и по адекватной цене. Буду обращаться еще.",
            rating=4,
            is_approved=True,
            ip="127.0.0.1",
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        command.stdout.write(command.style.SUCCESS("Demo reviews created."))
    else:
        command.stdout.write(command.style.WARNING("Reviews already exist."))
