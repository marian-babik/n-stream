if [ -f /usr/bin/disable_nstream ]; then
    chmod 755 /usr/bin/disable_nstream
fi

if [ -f /usr/bin/enable_nstream ]; then
    chmod 755 /usr/bin/enable_nstream
fi

if [ -f /usr/bin/mq_handler ]; then
    chmod 755 /usr/bin/mq_handler
fi

if [ -f /usr/bin/ocsp_handler ]; then
    chmod 755 /usr/bin/mq_handler
fi
