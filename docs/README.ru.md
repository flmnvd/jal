# JAL
Just Another Ledger - это проект для учета личных финансов

*[English](https://github.com/titov-vv/jal/blob/master/docs/README.md), [Русский](https://github.com/titov-vv/jal/blob/master/docs/README.ru.md)*

Он создавался чтобы учитывать личные доходы/расходы и инвестиции с актуальной информацией о состоянии счетов и оценочной стоимости портфеля ценных бумаг.

### Основные возможности
- ведение учета по нескольким счетам в разных валютах (основная валюта на данный момент - российскй рубль, в будущем планируетя добавть настройку основной валюты)
- 5 типов операций: 
    1. Обычный доход/расход, который может быть разделён на несколько категорий
    2. Перевод денежных средств между разными счетами и валютами
    3. Операции Покупки/Продажи ценных бумаг (*jal* поддерживает акции, облигации, опционы, частично поддерживает облигации и фьючерсы)
    4. Дивиденды по акциям и купонные выплаты по облигациям
    5. Корпоративные события для акций с учётом долей активов (Сплит, Смена символа, Выделение/Объединение компаний, Дивиденд акциями компании)
- основные отчеты:
    1. помесячный отчет доходов/расходов по категориям
    2. отчет о прибылях/убытках для инвестиционных счетов
    3. отчет по завершённым сделкам с ценными бумагами
- обновление котировок для американских (Yahoo), европейских (Euronext) и российских (MOEX) акций и ETF  
- импорт брокерских отчетов в формате Quik HTML для российских брокеров (КИТ-Финанс, Уралсиб брокер) и XML flex-отчетов для Interactive Brokers
- оценка предполагаемого налога к уплате по текущей котировке открытой позиции 
- налоговый отчет для подготовки декларации 3-НДФЛ по результатам операций с зарубежными ЦБ и заполнение файла программы Декларация (![инструкция](https://github.com/titov-vv/jal/blob/master/docs/ru-tax-3ndfl/taxes.md))
- *экспериментальная* функция загрузки электронных чеков с сайта ФНС (для использования этой функции вам понадобятся дополнительные зависимости - пакеты `pyzbar` и `Pillow`):
    1. QR-код может быть отсканирован камерой, либо распознан с изображения в буфере обмена или файле
    2. Для скачивания чеков нужна авторизация на сайте ФНС - программа поддерживает авторизацию через логин/пароль личного кабинете или Госуслуги (Пароли не сохраняются в программе, сохраняется только ID-сессии - можете проверить по исходному коду)
- *экспериментальное* распознавание категорий товаров из загруженных чеков с помощью `tensorflow` 
    

### Установка
*jal* создавался как переносимое приложение. Поэтому есть несколько способов установки программы:
- Вы можете скачать/клонировать код из [GitHub репозитория](https://github.com/titov-vv/jal), распаковать его в подходящий каталог на вашем компьютере и использовать `run.py` для старта приложения.
Чтобы всё сработало вам нужно иметь Python 3.8.1 и удовлетворить зависимости из `requirements.txt`.
- Вы можете установить пакет с помощью команды `pip install jal`. Она автоматически установит необходимые зависимости и создат скрипт `jal` для запуска<sup>*</sup> приложения.
Если установка пройдёт успешно, то вы сможете запускать приложение простой командой `jal`.
Также вы можете запустить приложение командой `python -m jal.jal`, если по какой-то причине вы не можете запустить её с помощью скрипта `jal`.
- Также можно смешать оба метода вместе - скачать исходный код с github и использовать `setup.py` удобным для вас способом.
он не требует каких-то специфичных инструкций по установке. Все что вам нужно - это иметь Python 3.8.1 или выше и установленные пакеты из раздела Зависимости.

База данных программы будет инициализирована автоматически минимально необходимым набором данных и вы сможете начать использовать приложение.

Для смены языка с Английского на Русский нужно выбрать пункт меню Languages->Russian и перезапустить программу

<sup>*</sup> - место создания скрипта зависит от операционной системы. Например, на Linux это может быть `~/.local/run`, на Windows - подкаталог `Scripts` каталога, где установлен python.

### Скриншоты
Основные скриншоты можно посмотреть на англоязычной версии данной страницы - они отличаются только языком.
Ниже представлены скриншоты функционала актуального только для России.

### Отчет по операциям с иностранными ценными бумагами

Отчёт может быть подготовлен по операциям любого брокера, если они присутствуют в программе, хотя ввод всех операций вручную может быть очень утомительной задачей.
На данный момент поддерживается импорт операций из отчётов Interactive Brokers. Пошаговая инструкция по подготовке данных для декларации 3-НДФЛ на основе отчет Interactive Brokers расположена на [отдельной странице](https://github.com/titov-vv/jal/blob/master/docs/ru-tax-3ndfl/taxes.md).
По вопросам поддержки отчётов других брокеров вы можете связаться со мной по адресу [jal@gmx.ru](mailto:jal@gmx.ru?subject=%5BJAL%5D%20Reports%20import).

### Загрузка электронных чеков с сайта ФНС

Диалог авторизации (выбрана страница с авторизацией через Госуслуги):  
![FSN authorization dialog](https://github.com/titov-vv/jal/blob/master/docs/img/fns_auth_dialog.png?raw=true)

Диалог импорта чека:  
![Electronic slip import dialog](https://github.com/titov-vv/jal/blob/master/docs/img/slip_import.png?raw=true) 

