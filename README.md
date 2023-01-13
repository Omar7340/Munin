# Munin

Projet IOT CNAM Janvier 2023

## Sujet 
![Sujet du projet](doc/sujet_iot.png)

Pour plus de précision voir __doc/Mineur IOT - Rapport d'analyse - Projet 1 - Omar OUHBAD et Mohamed-Ali BENZINA.pdf__

## Déploiement

Installation de docker et git

```bash
  sudo install.sh
```

Construction et déploiement des conteneurs docker

```bash
  sudo docker compose up
```

Après le démarrage des conteneurs, voici le fonctionnement normal de ce projet :
- La borne envoie les données sur Mosquitto
- Le centre de contrôle (côté agregateur) récupére les données sur le broker et les enregistre dans la base de données
- Le centre de contrôle (côté analyseur) récupère les données non analysées sur la base de données et les analysent (détection accident, détection embouteillage)
