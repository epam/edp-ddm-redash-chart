FROM nexus-docker-registry.apps.cicd2.mdtu-ddm.projects.epam.com/mdtu-ddm-edp-cicd/redash-1-9-8:1.9.8.4 as source

COPY translate.py /app/
COPY /locales /app/locales/
