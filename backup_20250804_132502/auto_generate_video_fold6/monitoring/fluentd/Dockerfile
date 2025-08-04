FROM fluent/fluentd:v1.16-debian-1

# Use root account to use apk
USER root

# 安裝必要的套件和插件
RUN buildDeps="sudo make gcc g++ libc-dev" \
 && apt-get update \
 && apt-get install -y --no-install-recommends $buildDeps \
 && sudo gem install fluent-plugin-elasticsearch \
 && sudo gem install fluent-plugin-prometheus \
 && sudo gem install fluent-plugin-systemd \
 && sudo gem install fluent-plugin-kubernetes_metadata_filter \
 && sudo gem install fluent-plugin-multi-format-parser \
 && sudo gem install fluent-plugin-json-in-json-2 \
 && sudo gem install fluent-plugin-docker_metadata_filter \
 && sudo gem install fluent-plugin-record-modifier \
 && SUDO_FORCE_REMOVE=yes \
    apt-get purge -y --auto-remove \
                  -o APT::AutoRemove::RecommendsImportant=false \
                  $buildDeps \
 && rm -rf /var/lib/apt/lists/* \
 && gem sources --clear-all \
 && rm -rf /tmp/* /var/tmp/* /usr/lib/ruby/gems/*/cache/*.gem

# 創建必要的目錄
RUN mkdir -p /fluentd/log /fluentd/etc /fluentd/plugins

# 複製配置文件
COPY fluent.conf /fluentd/etc/
COPY plugins /fluentd/plugins/

# 設置權限
RUN chown -R fluent /fluentd && chgrp -R fluent /fluentd

# 切換回 fluent 用戶
USER fluent

# 暴露端口
EXPOSE 24224 24220 9880

# 健康檢查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:9880/api/plugins.json || exit 1