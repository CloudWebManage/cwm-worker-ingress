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
redis-cli exists "hostname:initialize:${DOMAIN}"
```

Set domain available

```
redis-cli set "worker:available:${DOMAIN}" ""
```

Set domain internal host name to cwm-worker-test.com (You should also set an internal IP different then 127.0.0.1 for these domains in /etc/hosts)

```
redis-cli set "worker:ingress:hostname:${DOMAIN}" '{"http":"cwm-worker-test-http.com","https":"cwm-worker-test-https.com"}'
```

Set domain error

```
redis-cli set "worker:error:${DOMAIN}" ""
```

Set node healthy

```
redis-cli set "node:healthy:testnode0" ""
```

Check node healthy filename exists: `.node_healthy`

Delete node healthy

```
redis-cli del "node:healthy:testnode0"
```

Check node healthy filename deleted: `.node_healthy`

## Python module automated tests

Start the local development server as specified for local development

Set test domains in /etc/hosts:

```
172.17.0.1 cwm-worker-test-http.com
172.17.0.2 cwm-worker-test-https.com
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

## Local docker-compose production environment

Start the environment for serving http protocol (it uses network mode = host, so all ports should be free on the host)

```
docker-compose up --build -d
```

Set `localhost` domain to be available

```
redis-cli set "worker:available:localhost" ""
redis-cli set "worker:ingress:hostname:localhost" '{"http":"localhost"}'
```

Access it - should respond very quickly

```
time curl localhost
```

Set node healthy

```
redis-cli set "node:healthy:testnode0" ""
```

Get nginx healthz: `curl localhost/healthz` (should be OK)

Delete node healthy

```
redis-cli del "node:healthy:testnode0"
```

Get nginx healthz: `curl localhost/healthz` (should be error 404)

Run the stack for serving https:

```
docker-compose -f docker-compose.yaml -f docker-compose-https.yaml up --build -d
```

## Publishing Docker Images

Login to GitHub Packages, for password use a personal access token

```
docker login https://ghcr.io -u USERNAME
```

Build images

```
docker-compose build
```

Tag and push

```
docker tag cwm-worker-ingress_vdns:latest ghcr.io/cloudwebmanage/cwm-worker-ingress/vdns:latest &&\
docker tag cwm-worker-ingress_nginx:latest ghcr.io/cloudwebmanage/cwm-worker-ingress/nginx:latest &&\
docker push ghcr.io/cloudwebmanage/cwm-worker-ingress/vdns:latest &&\
docker push ghcr.io/cloudwebmanage/cwm-worker-ingress/nginx:latest
```

## Local Kubernetes production environment

### Install

Install Kubectl

```
curl -LO "https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl" &&\
chmod +x ./kubectl && sudo mv ./kubectl /usr/local/bin/kubectl
```

Install Minikube

```
curl -Lo minikube https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64 && chmod +x minikube &&\
sudo mv minikube /usr/local/bin/minikube
```

Install Helm

```
curl -Ls https://get.helm.sh/helm-v3.2.4-linux-amd64.tar.gz -ohelm.tar.gz &&\
tar -xzvf helm.tar.gz && sudo mv linux-amd64/helm /usr/local/bin/helm &&\
sudo chmod +x /usr/local/bin/helm &&\
rm -rf linux-amd64 && rm helm.tar.gz &&\
helm version
```

### Deployment

Create a cluster:

```shell
minikube start --driver=docker --kubernetes-version=v1.18.15
```

Verify connection to the cluster

```
kubectl get nodes
```

Deploy main redis server + tests objects

```
cat tests/k8s-tests.yaml | kubectl apply -f -
```

Verify main redis is running

```
kubectl exec redis -- redis-cli ping
```

Deploy using one of the following options:

* Use the published Docker images:
  * Deploy
    * `helm upgrade --install cwm-worker-ingress ./helm`

* Build your own Docker images:
  * Switch Docker daemon to use the minikube Docker daemon: `eval $(minikube -p minikube docker-env)`
```
docker-compose build &&\
docker tag cwm-worker-ingress_nginx:latest ghcr.io/cloudwebmanage/cwm-worker-ingress/nginx:latest &&\
docker tag cwm-worker-ingress_vdns:latest ghcr.io/cloudwebmanage/cwm-worker-ingress/vdns:latest &&\
helm upgrade --install --wait --set "vdns.debugVerbosity=8,debug=true" cwm-worker-ingress ./helm
```

Run k8s tests

```
tests/k8s_tests.sh
```

## testing VDNS server scale limit

Start with 2 threads

```
UDP_THREADS=2 DEBUG=yes REDIS_HOST=172.17.0.1 venv/bin/cwm_worker_ingress vdns 10053
```

Generate load (change number depending on your processing power)

```
python3 tests/load_generator.py 500
```

You should see some processes failed like this:

```
372: returncode 1 output b';; connection timed out; no servers could be reached\n\n\n'
```
