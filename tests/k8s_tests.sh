#!/usr/bin/env bash

ELAPSED_SECONDS=0
while true; do
  sleep 1 && ELAPSED_SECONDS="$(expr $ELAPSED_SECONDS + 1)"
  kubectl get ds cwm-worker-ingress -o yaml | grep 'numberReady: 1' &&\
  [ "$(kubectl get pods | grep Running | wc -l)" == "3" ] &&\
  kubectl get pods | grep cwm-worker-ingress | grep ' 3/3 ' &&\
  kubectl get pods | grep redis | grep ' 1/1 ' &&\
  kubectl get pods | grep tests | grep ' 1/1 ' &&\
  break
  [ "${ELAPSED_SECONDS}" == "30" ] && echo waited too long for pods to be ready && exit 1
done

kubectl exec redis -- redis-cli del worker:available:tests.cwm-worker-ingress.com &&\
kubectl exec redis -- redis-cli del worker:ingress:hostname:tests.cwm-worker-ingress.com &&\
kubectl exec redis -- redis-cli del worker:initialize:tests.cwm-worker-ingress.com
[ "$?" != "0" ] && echo failed to clear redis && exit 1

sleep 2

if OUTPUT="$(/usr/bin/time -f "%e" kubectl exec tests -- curl -sH 'Host: tests.cwm-worker-ingress.com' http://cwm-worker-ingress | grep 'Thank you for using nginx')"; then
  echo "${OUTPUT}"
  echo request to tests.cwm-worker-ingress.com was successfull, expected it to fail
  exit 1
fi
if [ "$(expr "${OUTPUT} < 5")" == "1" ]; then
  echo request to tests.cwm-worker-ingress.com was too quick, expected it to take 5 seconds
  exit 1
fi

if [ "$(kubectl exec redis -- redis-cli exists worker:initialize:tests.cwm-worker-ingress.com)" != "1" ]; then
  echo initialize request for tests.cwm-worker-ingress.com was not avaialble in main redis
  exit 1
fi

kubectl exec redis -- redis-cli set worker:available:tests2.cwm-worker-ingress.com "" &&\
kubectl exec redis -- redis-cli set worker:ingress:hostname:tests2.cwm-worker-ingress.com "tests.default.svc.cluster.local" &&\
kubectl exec redis -- redis-cli del worker:initialize:tests2.cwm-worker-ingress.com
[ "$?" != "0" ] && echo failed to set redis values && exit 1

if ! OUTPUT="$(/usr/bin/time -f "%e" kubectl exec tests -- curl -sH 'Host: tests2.cwm-worker-ingress.com' http://cwm-worker-ingress | grep 'Thank you for using nginx')"; then
  echo "${OUTPUT}"
  echo request to tests2 failed, expected it to succeed
  exit 1
fi
if [ "$(expr "${OUTPUT} > 1")" == "1" ]; then
  echo request to tests2 took too long
  exit 1
fi

echo OK
exit 0