"""
Общие константы бизнес-логики (значения по умолчанию; часть настраивается в БД).
"""

# Максимум активных записей атлета на один календарный день (дефолт; админ меняет в вебе)
DEFAULT_MAX_BOOKINGS_PER_DAY = 2
MIN_MAX_BOOKINGS_PER_DAY = 1
MAX_MAX_BOOKINGS_PER_DAY = 20

SETTING_KEY_MAX_BOOKINGS_PER_DAY = "max_bookings_per_day"
