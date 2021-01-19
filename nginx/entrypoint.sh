#!/usr/bin/env sh

if [ "${METRIC_LUA_WITH_HOST}" == "yes" ]; then
  echo metrics with host
  echo "include metric_lua_with_host.conf;" > /usr/local/openresty/nginx/conf/metric_lua.conf
else
  echo metrics without host
fi

exec /usr/local/openresty/bin/openresty -g "daemon off;"
