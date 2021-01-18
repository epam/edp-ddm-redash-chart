FROM redash/redash:8.0.2.b37747 as source

FROM python:3.9.6 as local
COPY --from=source /app/client/dist/app.*.js /app/
COPY --from=source /app/redash/cli/users.py /app/redash/cli/
COPY --from=source /app/redash/handlers/setup.py /app/redash/handlers/
COPY --from=source /app/redash/models/__init__.py /app/redash/models/
COPY --from=source /app/redash/models/users.py /app/redash/models
COPY . /app
WORKDIR /app
RUN pip install pipenv
RUN pipenv install
RUN pipenv run python main.py

FROM source
COPY --from=local /app/app.*.js /app/client/dist/.
COPY --from=local /app/redash/cli/users.py /app/redash/cli/
COPY --from=local /app/redash/handlers/setup.py /app/redash/handlers/
COPY --from=local /app/redash/models/__init__.py /app/redash/models/
COPY --from=local /app/redash/models/users.py /app/redash/models/
