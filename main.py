"""
Точка входа в приложение
"""
from src.bot import TelegramBot


def main():
    """Главная функция"""
    bot = TelegramBot()
    bot.run()


if __name__ == '__main__':
    main()

