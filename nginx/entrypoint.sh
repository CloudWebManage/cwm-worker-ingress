#!/usr/bin/env sh

if [ "${METRIC_LUA_DISABLE}" == "yes" ]; then
  echo metrics disabled
  echo "" > /usr/local/openresty/nginx/conf/metric_lua.conf
  echo "" > /usr/local/openresty/nginx/conf/metric_lua_http.conf
  echo "" > /usr/local/openresty/nginx/conf/metric_lua_https.conf
else
  # metrics with host is not supported for SSL
  #if [ "${METRIC_LUA_WITH_HOST}" == "yes" ]; then
  #  echo metrics with host
  #  echo "include metric_lua_with_host.conf;" > /usr/local/openresty/nginx/conf/metric_lua.conf
  #else
    echo metrics without host
  #fi
fi

if [ "${ENABLE_ACCESS_LOG}" == "yes" ]; then
  echo access log enabled
else
  echo access log disabled
  echo "" > /usr/local/openresty/nginx/conf/access_log.conf
fi

if [ "${CWM_NGINX_PROTOCOL}" == "https" ]; then
  echo serving cwm https
  cat /usr/local/openresty/nginx/conf/nginx_https.conf > /usr/local/openresty/nginx/conf/nginx.conf
else
  echo serving cwm http
  cat /usr/local/openresty/nginx/conf/nginx_http.conf > /usr/local/openresty/nginx/conf/nginx.conf
fi

if [ "${WORKER_PROCESSES}" != "" ]; then
  sed -i "s/worker_processes 1;/worker_processes ${WORKER_PROCESSES};/g" /usr/local/openresty/nginx/conf/nginx.conf
fi

if [ "${WORKER_CONNECTIONS}" != "" ]; then
  sed -i "s/worker_connections 2048;/worker_connections ${WORKER_CONNECTIONS};/g" /usr/local/openresty/nginx/conf/nginx.conf
fi

exec /usr/local/openresty/bin/openresty -g "daemon off;"
