#!/usr/bin/env bash

set -eE -o functrace

failure() {
  local lineno=$1
  local msg=$2
  echo "Failed at $lineno: $msg"
}
trap 'failure ${LINENO} "$BASH_COMMAND"' ERR

sudo apt-get install -y redis-tools
python -m venv venv
venv/bin/pip install --upgrade pip
venv/bin/python -m pip install -r requirements.txt
venv/bin/python -m pip install -e .

docker run -d --rm --name redis -p 6379:6379 redis
[ "$?" != "0" ] && echo failed to initialize for tests && exit 1
while ! redis-cli ping; do sleep 1; done
DEBUG=yes REDIS_HOST=172.17.0.1 venv/bin/cwm_worker_ingress vdns 10053 >log.txt 2>&1 &
sleep 2

echo 172.17.0.1 cwm-worker-test-http.com | sudo tee -a /etc/hosts
echo 172.17.0.2 cwm-worker-test-https.com | sudo tee -a /etc/hosts

. venv/bin/activate
[ "$?" != "0" ] && exit 1
echo ERROR > status.txt

( ./run_tests.sh && echo OK > status.txt ) & PID=$!
ELAPSED_SECONDS=0
while true; do
    sleep 1 && ELAPSED_SECONDS="$(expr $ELAPSED_SECONDS + 1)"
    ! ps -p $PID > /dev/null && break
    [ "${ELAPSED_SECONDS}" == "60" ] && echo TIMEOUT > status.txt && break
done

echo "status.txt=$(cat status.txt)"
echo "-- vdns server log --"
cat log.txt
[ "$(cat status.txt)" != "OK" ] && echo tests failed && exit 1
deactivate

uci github actions docker-login
uci docker build-cache \
    --cache-from ghcr.io/cloudwebmanage/cwm-worker-ingress/vdns:latest \
    -- -t vdns .
uci docker build-cache \
    --cache-from ghcr.io/cloudwebmanage/cwm-worker-ingress/nginx:latest \
    -- -t nginx nginx
uci docker tag-push \
    --source-tag-name vdns \
    --push-tag-name "ghcr.io/cloudwebmanage/cwm-worker-ingress/vdns:$GITHUB_SHA"
uci docker tag-push \
    --source-tag-name nginx \
    --push-tag-name "ghcr.io/cloudwebmanage/cwm-worker-ingress/nginx:$GITHUB_SHA"

# if [ "$(uci github actions get-branch-name)" == "master" ]; then
    uci docker tag-push \
        --source-tag-name vdns \
        --push-tag-name ghcr.io/cloudwebmanage/cwm-worker-ingress/vdns:latest
    uci docker tag-push \
        --source-tag-name nginx \
        --push-tag-name ghcr.io/cloudwebmanage/cwm-worker-ingress/nginx:latest
    uci kubectl install --version "${KUBECTL_VERSION}" --with-sudo
    uci minikube install --version "${MINIKUBE_VERSION}" --with-sudo
    uci helm install --version "${HELM_VERSION}" --with-sudo
    minikube start --driver=docker --kubernetes-version="${MINIKUBE_KUBERNETES_VERSION}"
    uci util wait-for --timeout-seconds 240 --timeout-message "waited too long for minikube to start" \
        "minikube status 2>&1 >/dev/null"
    uci util wait-for --timeout-seconds 240 --timeout-message "waited too long for minikube node to be ready" \
        'kubectl get nodes | grep " Ready "'
    helm upgrade --install --wait cwm-worker-ingress ./helm
    sleep 5
    kubectl apply -f tests/k8s-tests.yaml
    [ "$?" != "0" ] && echo "failed to apply tests/k8s-tests.yaml" && exit 1
    sleep 10
    tests/k8s_tests.sh
    K8S_TESTS_RES="$?"
    echo K8S_TESTS_RES=$K8S_TESTS_RES
    POD=$(kubectl get pods | grep cwm-worker-ingress-http- | tee /dev/stderr | cut -d " " -f1)
    kubectl describe pod tests
    kubectl describe pod "$POD"
    echo "-- redis logs --"
    kubectl logs $POD -c redis
    echo "-- nginx logs --"
    kubectl logs $POD -c nginx
    echo "-- vdns logs --"
    kubectl logs $POD -c vdns
    echo "---------------"
    # [ "${K8S_TESTS_RES}" != "0" ] && echo "K8S_TESTS_RES=$K8S_TESTS_RES" && exit 1
    # uci git checkout \
    #     --github-repo-name CloudWebManage/cwm-worker-helm \
    #     --branch-name master \
    #     --ssh-key "${CWM_WORKER_HELM_DEPLOY_KEY}" \
    #     --path cwm-worker-helm \
    #     --config-user-name cwm-worker-ingress-ci
    # sed -i "s/appVersion: latest/appVersion: ${GITHUB_SHA}/g" helm/Chart.yaml
    # helm package ./helm --version "0.0.0-$(date +%Y%m%dT%H%M%S)" --destination ./cwm-worker-helm/cwm-worker-ingress
    # helm repo index --url "https://raw.githubusercontent.com/CloudWebManage/cwm-worker-helm/master/cwm-worker-ingress/" \
    #     ./cwm-worker-helm/cwm-worker-ingress
    # cd cwm-worker-helm
    # git add cwm-worker-ingress
    # git commit -m "automatic update of cwm-worker-ingress"
    # git push origin master
# fi
