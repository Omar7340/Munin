# Munin

Projet IOT CNAM Janvier 2023

## Sujet 
![Sujet du projet](doc/sujet_iot.png)

Pour plus de précision voir __doc/Mineur IOT - Rapport d'analyse - Projet 1 - Omar OUHBAD et Mohamed-Ali BENZINA.pdf__

## Déploiement

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

Une fois les conteneurs démarrés, les données sont envoyées sur le broker par la borne puis elles seront récupérés par le centre de contrôle (CDC) dans le broker et stocké dans la base de donées.
