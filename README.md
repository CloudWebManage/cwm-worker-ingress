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

## Local docker-compose production environment

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

## Publishing Docker Images

Login to GitHub Packages, for password use a personal access token

```
docker login https://docker.pkg.github.com -u USERNAME
```

Build images

```
docker-compose build
```

Tag and push

```
docker tag cwm-worker-ingress_vdns:latest docker.pkg.github.com/cloudwebmanage/cwm-worker-ingress/vdns:latest &&\
docker tag cwm-worker-ingress_nginx:latest docker.pkg.github.com/cloudwebmanage/cwm-worker-ingress/nginx:latest &&\
docker push docker.pkg.github.com/cloudwebmanage/cwm-worker-ingress/vdns:latest &&\
docker push docker.pkg.github.com/cloudwebmanage/cwm-worker-ingress/nginx:latest
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

Create a cluster

```
minikube start --driver=docker --kubernetes-version=v1.16.14
```

Verify connection to the cluster

```
kubectl get nodes
```

Set your GitHub username and token in env vars

```
GITHUB_USER=
GITHUB_TOKEN=
```

Create a docker pull secret

```
echo '{"auths":{"docker.pkg.github.com":{"auth":"'"$(echo -n "${GITHUB_USER}:${GITHUB_TOKEN}" | base64)"'"}}}' \
    | kubectl -- create secret generic github --type=kubernetes.io/dockerconfigjson --from-file=.dockerconfigjson=/dev/stdin
```

Deploy

```
helm upgrade --install cwm-worker-ingress ./helm
```

### Test

Deploy tests objects

```
cat tests/k8s-tests.yaml | kubectl apply -f -
```

Set keys in Redis

```
kubectl exec -c redis "$(kubectl get pods | grep cwm-worker-ingress | cut -d" " -f 1)" -- redis-cli set worker:available:tests.cwm-worker-ingress.com "" &&\
kubectl exec -c redis "$(kubectl get pods | grep cwm-worker-ingress | cut -d" " -f 1)" -- redis-cli set worker:ingress:hostname:tests.cwm-worker-ingress.com "tests.default.svc.cluster.local"
```

Run test

```
kubectl exec tests -- curl -H 'Host: tests.cwm-worker-ingress.com' http://cwm-worker-ingress | grep 'Thank you for using nginx'
```

