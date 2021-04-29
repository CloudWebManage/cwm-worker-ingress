#!/usr/bin/env bash

ELAPSED_SECONDS=0
while true; do
  sleep 1 && ELAPSED_SECONDS="$(expr $ELAPSED_SECONDS + 1)"
  kubectl get ds cwm-worker-ingress-http -o yaml | grep 'numberReady: 1' &&\
  kubectl get ds cwm-worker-ingress-https -o yaml | grep 'numberReady: 1' &&\
  [ "$(kubectl get pods | grep Running | wc -l)" == "4" ] &&\
  kubectl get pods | grep cwm-worker-ingress-http | grep ' 3/3 ' &&\
  kubectl get pods | grep cwm-worker-ingress-https | grep ' 3/3 ' &&\
  kubectl get pods | grep redis | grep ' 1/1 ' &&\
  kubectl get pods | grep tests | grep ' 1/1 ' &&\
  break
  [ "${ELAPSED_SECONDS}" == "30" ] && echo waited too long for pods to be ready && exit 1
done

kubectl exec redis -- redis-cli del hostname:available:tests.cwm-worker-ingress.com &&\
kubectl exec redis -- redis-cli del hostname:ingress:hostname:tests.cwm-worker-ingress.com &&\
kubectl exec redis -- redis-cli del hostname:initialize:tests.cwm-worker-ingress.com
[ "$?" != "0" ] && echo failed to clear redis && exit 1

sleep 2

if OUTPUT="$(/usr/bin/time -f "%e" kubectl exec tests -- curl -sH 'Host: tests.cwm-worker-ingress.com' http://cwm-worker-ingress-http | grep 'Thank you for using nginx')"; then
  echo "${OUTPUT}"
  echo request to tests.cwm-worker-ingress.com was successfull, expected it to fail
  exit 1
fi
if [ "$(expr "${OUTPUT} < 5")" == "1" ]; then
  echo request to tests.cwm-worker-ingress.com was too quick, expected it to take 5 seconds
  exit 1
fi

if [ "$(kubectl exec redis -- redis-cli exists hostname:initialize:tests.cwm-worker-ingress.com)" != "1" ]; then
  echo initialize request for tests.cwm-worker-ingress.com was not avaialble in main redis
  exit 1
fi

kubectl exec redis -- redis-cli set hostname:available:tests2.cwm-worker-ingress.com "" &&\
kubectl exec redis -- redis-cli set hostname:ingress:hostname:tests2.cwm-worker-ingress.com '{"http":"tests.default.svc.cluster.local","https":"tests.default.svc.cluster.local"}' &&\
kubectl exec redis -- redis-cli del hostname:initialize:tests2.cwm-worker-ingress.com
[ "$?" != "0" ] && echo failed to set redis values && exit 1

if ! OUTPUT="$(/usr/bin/time -f "%e" kubectl exec tests -- curl -sH 'Host: tests2.cwm-worker-ingress.com' http://cwm-worker-ingress-http | grep 'Thank you for using nginx')"; then
  echo "${OUTPUT}"
  echo request to tests2 http failed, expected it to succeed
  exit 1
fi
if [ "$(expr "${OUTPUT} > 1")" == "1" ]; then
  echo request to tests2 http took too long
  exit 1
fi

kubectl exec redis -- redis-cli del node:healthy:minikube
sleep 1
if ! kubectl exec tests -- curl -s http://cwm-worker-ingress-http/healthz | grep "404 Not Found"; then
  echo after delete of node healthy redis key healthz response was not 404
  exit 1
fi
kubectl exec redis -- redis-cli set node:healthy:minikube ""
sleep 1
if ! kubectl exec tests -- curl -s http://cwm-worker-ingress-http/healthz | grep "OK"; then
  echo after set of node healthy redis key healthz response was not OK
  exit 1
fi

echo OK
exit 0