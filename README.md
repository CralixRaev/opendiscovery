# OpenDiscovery

[![CI](https://github.com/CralixRaev/opendiscovery/actions/workflows/ci.yml/badge.svg?branch=dev)](https://github.com/CralixRaev/opendiscovery/actions/workflows/ci.yml)

Обнаружение сетевых ресурсов в сети и их визуализация

## Цель
Построить мульти-тенантную платформу для поиска разными сканерами (для MVP только nmap) сетевых ресурсов в сети.

## Основной функционал (для MVP)
* Мультитенатная среда
* Добавление сканеров для разных тенатнов
* Передача заданий из control-plane в сканеры разных тенантов
* Визуализаций CMDB для отсканированных ресурсов
* Построение диаграммы количества хостов и количества открытых уязвимых портов

## Ограничения (из-за того, что это вузовский проект)
Без ORM :(

## Участники
Строю в одиночку :)

Лид, архитектор, бэк, фронт, qa, scrum и все остальное - Анатолий Раев
(https://github.com/CralixRaev/opendiscovery/)

плюс помощь нейросетей, конечно же (можно же фронт с помощью них чутка дописывать...?)

## Архитектура и технологии
Микросервисная архитектура. Все поделено на control plane (основной веб интерфейс, плюс контроль заданий на сканирование)
и на scan domain - сами сканеры тенантов.
Сканеры тенантов через NATS.io получают из своей очереди получают задание, его выполняют и складывают обратно

Все остальное тоже ходит через NATS.io

Технологии:
* Основные микросервисы - FastAPI
* Сами сканеры - никаких космических фреймворкой, скорее всего сырой питон
* Очередь сообщений - NATS.io
* Фронт - React
* База - PostgreSQL

## Запуск в Docker

Для локального запуска можно сразу поднять весь control-plane стек:

```bash
docker compose up --build
```

Frontend будет доступен на `http://localhost:3000`, backend API - на `http://localhost:8000`.

В compose уже есть dev `AUTH_ISSUER_SEED`, который соответствует `authorization.auth_callout.issuer`
в `configs/natsio.conf`. Для production замените пару ключей:

```bash
cp .env.example .env
```

Если генерируете новый account nkey через `nsc generate nkey --account`, положите seed
в `.env`, а public key пропишите в `configs/natsio.conf`.

Scanner-клиент запускается отдельным profile, потому что ему нужен токен созданного сканера:

```bash
OPENDISCOVERY_SCANNER_TOKEN="<token from UI/API>" docker compose --profile scanner up --build scanner
```
