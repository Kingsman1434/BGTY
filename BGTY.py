import logging
from selenium import webdriver
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import time

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Настройка драйвера
def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Запуск в фоновом режиме без GUI
    chrome_options.add_argument("--no-sandbox")  # Для некоторых сред выполнения
    chrome_options.add_argument("--disable-dev-shm-usage")  # Для предотвращения ошибок на системах с ограниченной памятью
    chrome_options.add_argument("--window-size=1920x1080")  # Задать размер окна

    try:
        # Используем WebDriverManager для автоматического выбора версии chromedriver
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        logging.info("Драйвер успешно запущен в headless-режиме.")
        return driver
    except Exception as e:
        logging.error(f"Ошибка при запуске драйвера: {e}")
        raise

# Открытие веб-страницы
def open_page(driver, url):
    try:
        driver.get(url)
        logging.info("Страница успешно загружена.")
    except Exception as e:
        logging.error(f"Ошибка при загрузке страницы '{url}': {e}")
        raise

# Выбор опции из выпадающего списка
def select_option(driver, select_id, value):
    try:
        select_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, select_id))
        )
        select = Select(select_element)
        try:
            select.select_by_visible_text(value)
            logging.info(f"Выбрано значение '{value}' в списке '{select_id}'")
        except NoSuchElementException:
            logging.warning(f"Значение '{value}' не найдено в списке '{select_id}', попробуем ввести вручную.")
            select_element.send_keys(value)
        time.sleep(1)  # Задержка в 1 секунду
    except TimeoutException as e:
        logging.error(f"Ошибка при выборе значения '{value}' в списке '{select_id}': {e}")
        raise

# Определение текущей недели (четная или нечетная) из заголовка страницы
def get_week_type(driver):
    try:
        header_element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'ttlpage'))
        )
        page_title = header_element.text.strip()

        if "четная неделя" in page_title:
            logging.info("Определена четная неделя.")
            return True
        elif "нечетная неделя" in page_title:
            logging.info("Определена нечетная неделя.")
            return False
        else:
            logging.warning("Не удалось однозначно определить тип недели, будут учтены оба варианта.")
            return None
    except TimeoutException as e:
        logging.error(f"Ошибка при определении типа недели: {e}")
        raise

# Извлечение данных из таблицы
def extract_table_data(driver):
    try:
        is_even_week = get_week_type(driver)  # Определение типа недели
        table_element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, '//table[@class="contless"]'))
        )
        rows = table_element.find_elements(By.TAG_NAME, 'tr')

        days_schedule = {}
        current_day = None

        for row in rows:
            try:
                day_elements = row.find_elements(By.CLASS_NAME, 'daeweek')
                if day_elements:
                    current_day = day_elements[0].text.strip()
                    days_schedule[current_day] = []
                else:
                    time_cells = row.find_elements(By.CLASS_NAME, 'schtime')
                    if len(time_cells) > 1:
                        time_cell_index = 1 if is_even_week else 0
                        time_cell = time_cells[time_cell_index] if time_cell_index < len(time_cells) else None
                    else:
                        time_cell = time_cells[0] if time_cells else None

                    name_cell = row.find_element(By.CLASS_NAME, 'schname') if row.find_elements(By.CLASS_NAME, 'schname') else None
                    teacher_cell = row.find_element(By.CLASS_NAME, 'schteacher') if row.find_elements(By.CLASS_NAME, 'schteacher') else None
                    class_cell = row.find_element(By.CLASS_NAME, 'schclass') if row.find_elements(By.CLASS_NAME, 'schclass') else None

                    time = time_cell.text.strip() if time_cell else ''
                    name = name_cell.text.strip().replace('\n', ' ') if name_cell else ''
                    teacher = teacher_cell.text.strip().replace('\n', ' ') if teacher_cell else ''
                    class_room = class_cell.text.strip() if class_cell else ''

                    if current_day:
                        days_schedule[current_day].append([time, name, teacher, class_room])
            except Exception as e:
                logging.error(f"Ошибка при обработке строки таблицы: {e}")

        for day, classes in days_schedule.items():
            print(f"\n{day}")
            print(f"{'Time':<15} {'Name':<50} {'Teacher':<30} {'Class':<10}")
            for cls in classes:
                print(f"{cls[0]:<15} {cls[1]:<50} {cls[2]:<30} {cls[3]:<10}")

        logging.info("Данные успешно извлечены и выведены на экран.")
    except Exception as e:
        logging.error(f"Ошибка при извлечении данных из таблицы: {e}")
        raise

# Основной процесс
def main():
    driver = None
    try:
        driver = setup_driver()
        open_page(driver, 'https://www.tu-bryansk.ru/education/schedule/')
        select_option(driver, 'period', '2024-2025: 1 семестр')
        select_option(driver, 'faculty', 'Факультет информационных технологий')
        select_option(driver, 'level', 'бакалавр')
        select_option(driver, 'group', 'О-24-ИБ-2-ози-Б')
        extract_table_data(driver)
    except Exception as e:
        logging.error(f"Ошибка в основном процессе: {e}")
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
