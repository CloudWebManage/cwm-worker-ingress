# cwm-worker-ingress

## Local development

### Install

Create virtualenv

```
python3 -m venv venv
```

Install dependencies

```
venv/bin/python -m pip install -r requirements.txt
```

Install cwm-worker-ingress Python module

```
venv/bin/python -m pip install -e .
```

### Usage

Start a Redis server

```
docker run -d --rm --name redis -p 6379:6379 redis
```

Start the VDNS server in debug mode on port 10053 with connection to the Redis

```
DEBUG=yes REDIS_HOST=172.17.0.1 venv/bin/cwm_worker_ingress vdns 10053
```

Set a domain for testing in env var:

```
DOMAIN=foobar.com
```

Use nslookup to make a request to the server

```
nslookup -port=10053 "${DOMAIN}" - 127.0.0.1
```

Use the following commands to test the Redis data:

Check if domain asked to be initialized (response should be = 1)

```
redis-cli exists "worker:initialize:${DOMAIN}"
```

Set domain available

```
redis-cli set "worker:available:${DOMAIN}" ""
```

Set domain internal host name to cwm-worker-test.com (You should also set an internal IP for it in /etc/hosts)

```
redis-cli set "worker:ingress:hostname:${DOMAIN}" "cwm-worker-test.com"
```

Set domain error

```
redis-cli set "worker:error:${DOMAIN}" ""
```

## Python module automated tests

Start the local development server as specified for local development

Set test domain in /etc/hosts:

```
172.17.0.1 cwm-worker-test.com
```

Make sure to start a clean Redis

```
docker rm -f redis
docker run -d --rm --name redis -p 6379:6379 redis
```

Activate the virtualenv

```
. venv/bin/activate
```

Run all tests:

```
./run_tests.sh
```

## Testing production deployment

Start the environment (it uses network mode = host, so all ports should be free on the host)

```
docker-compose up --build -d
```

Set `localhost` domain to be available

```
redis-cli set "worker:available:localhost" ""
redis-cli set "worker:ingress:hostname:localhost" "localhost"
```

Access it - should respond very quickly

```
time curl localhost
```
