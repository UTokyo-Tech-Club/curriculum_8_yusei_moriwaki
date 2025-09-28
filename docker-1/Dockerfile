FROM ubuntu:latest

COPY os9.txt /os9.txt

RUN set -eu; \
    mkdir -p /obento; \
    echo 'ツナマヨ' > /obento/onigiri

CMD ["cat", "/obento/onigiri"]