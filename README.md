## Описание сервиса
![alt text](images/service.jpg)
Простенький сервис для отслеживания достижений. Пользователь может добавить достижение, указав его название и вес. Достижения отображаются в истории пропорционально их весу.


docker-compose.yml включает три сервиса:

- postgres: база данных; хранит достижения
- init-db: инициализация базы данных.
- web: Streamlit приложение


## Запуск сервиса
```bash
# for initial run
docker compose run --rm web python src/database/init_db.py
docker compose up
```

## Ответы на вопросы:

> Можно ли ограничивать ресурсы (например, память или CPU) для сервисов в docker-compose.yml? Если нет, то почему, если да, то как?

Да, в docker-compose.yml можно ограничивать ресурсы для сервисов.

```yaml
services:
  web:
    deploy:
      resources:
        limits:
          cpus: '0.50'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

> Как можно запустить только определенный сервис из docker-compose.yml, не запуская остальные?

```bash
docker-compose up <name>
```
E.g.
```bash
docker-compose up web
```
