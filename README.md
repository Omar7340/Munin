# Munin

Projet IOT CNAM Janvier 2023

## Sujet 
![Sujet du projet](doc/sujet_iot.png)

Pour plus de précision voir __doc/Mineur IOT - Rapport d'analyse - Projet 1 - Omar OUHBAD et Mohamed-Ali BENZINA.pdf__

## Deployment

Instruction pour deployer sur une machine virtuelle remotlabz.

Installation de docket et git

```bash
  sudo install.sh
```

Construction et Deploiement des containers docker

```bash
  sudo docker compose up
```

L'installation du conteneur de base de données prend plusieurs minutes.


Donc les conteneurs de Grafana et des différents scripts redémarreront tant qu'ils ne seront pas connectés à la base.


