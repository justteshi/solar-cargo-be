![Screenshot](backend/reports/static/images/solar_cargo_logo.jpg)
# solar-cargo-be
### 1. Create .env 
```
POSTGRES_DB=solarCargoDb
POSTGRES_USER=solarCargoDbUser
POSTGRES_PASSWORD=solarCargoSuperSecretDbPassword
```
### 2. Build and start containers
```
docker compose up --build
```
### 3. Jump into web container
```
docker exec -it container_name bash
```
### 4. Run migrations
```
python manage.py migrate
```
### 5. (Optional) Create upser user for DJango admin
```
python manage.py createsuperuser
```
