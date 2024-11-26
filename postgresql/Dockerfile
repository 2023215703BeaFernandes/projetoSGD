# 
# Sistema de Gestão de Dados 2024/2025
# Trabalho Prático
#
# Authors: 
#   SGD 2024 Team
#   University of Coimbra

FROM library/postgres


ENV POSTGRES_USER projetosgd
ENV POSTGRES_PASSWORD projetosgd
ENV POSTGRES_DB companhiaaerea

COPY SGD2024_data.sql /docker-entrypoint-initdb.d/

EXPOSE 5432
