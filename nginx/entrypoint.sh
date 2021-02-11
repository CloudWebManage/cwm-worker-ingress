#!/usr/bin/env sh

# metrics with host is not supported for SSL
#if [ "${METRIC_LUA_WITH_HOST}" == "yes" ]; then
#  echo metrics with host
#  echo "include metric_lua_with_host.conf;" > /usr/local/openresty/nginx/conf/metric_lua.conf
#else
echo metrics without host
#fi

if [ "${CWM_NGINX_PROTOCOL}" == "https" ]; then
  echo serving cwm https
  cat /usr/local/openresty/nginx/conf/nginx_https.conf > /usr/local/openresty/nginx/conf/nginx.conf
else
  echo serving cwm http
  cat /usr/local/openresty/nginx/conf/nginx_http.conf > /usr/local/openresty/nginx/conf/nginx.conf
fi

exec /usr/local/openresty/bin/openresty -g "daemon off;"
