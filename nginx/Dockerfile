FROM openresty/openresty:1.19.3.1-2-alpine
RUN apk add --no-cache curl perl
RUN opm get knyar/nginx-lua-prometheus=0.20201218
COPY nginx_http.conf nginx_https.conf resolver.conf http_listen.conf https_listen.conf \
     extra-pre.conf extra-post.conf \
     metric_lua.conf metric_lua_with_host.conf metric_lua_without_host.conf \
     entrypoint.sh \
         /usr/local/openresty/nginx/conf/
ENTRYPOINT ["/usr/local/openresty/nginx/conf/entrypoint.sh"]
