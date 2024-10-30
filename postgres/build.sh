#!/bin/bash
# 
# Sistema de Gestão de Dados 2024/2025
# Trabalho Prático
#
# Authors: 
#   SGD 2024 Team
#   University of Coimbra

image="bd-psql"
container="db"



echo "-- Building --"
docker  build  -t  $image   .