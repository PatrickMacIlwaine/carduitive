#!/bin/sh
RESOLVER=$(awk '/^nameserver/{print $2; exit}' /etc/resolv.conf)
SEARCH=$(awk '/^search/{print $2; exit}' /etc/resolv.conf)

# In k8s with hostNetwork, short names don't resolve — use FQDN
if echo "$SEARCH" | grep -q "svc.cluster.local"; then
    BACKEND_HOST="backend.${SEARCH}"
else
    BACKEND_HOST="backend"
fi

sed -i "s/__RESOLVER__/$RESOLVER/" /etc/nginx/conf.d/default.conf
sed -i "s/__BACKEND_HOST__/$BACKEND_HOST/" /etc/nginx/conf.d/default.conf
exec nginx -g 'daemon off;'
