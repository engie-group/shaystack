FROM python:3

WORKDIR /usr/src/app

# Use the published module in test
ENV PIP_INDEX_URL=https://test.pypi.org/simple
ENV PIP_EXTRA_INDEX_URL=https://pypi.org/simple
RUN pip install --no-cache-dir "haystackapi[flask,graphql,lambda]"

COPY sample sample

ENV HAYSTACK_PROVIDER=haystackapi.providers.url
ENV HAYSTACK_URL=sample/carytown.zinc
ENV HAYSTACK_DB=sqlite:///test.db#haystack
ENV HAYSTACK_DB_SECRET=
ENV REFRESH=15

CMD [ "haystackapi" ]