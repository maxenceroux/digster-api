# FastAPI for Digster API

# Activate virtual env
```sh
poetry shell
code .
```
# Run
## Locally
```sh
make start-local
```
# Test
```sh
make test-local
```
## With coverage
```sh
make test-cov-local
```
# Migrate
```sh
make migrate-db
```

# Todo
- Check post to put endpoints
- change sql request to extract tracks using timestamp strategy
- Review typings on `spotify_controller.py`
- Integration tests
