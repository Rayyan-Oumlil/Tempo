# Faire tourner Tempo sur un VPS (sans ton PC)

Durée: environ 45 minutes la première fois. Coût: ~12 USD/mois (DigitalOcean Basic, 2 GiB / 1 vCPU, IPv4 incluse).

**Règle d'or:** un seul Tempo à la fois. Le journal des ordres (`journal/`) n'est pas dans git. Si le PC et le VPS lancent
tous les deux `entries`, ils peuvent trader deux fois. On coupe le PC (étape 4) **avant** d'allumer le VPS (étape 6).

## Installation réelle (2026-11-11, OVH VPS, Ubuntu 24.04)
Ce qui a différé du guide DigitalOcean ci-dessous:
- OVH crée l'utilisateur **`ubuntu`** (pas `root`) avec un mot de passe temporaire à changer à la première connexion (terminal requis). Ensuite, ajouter la clé SSH du PC dans `~/.ssh/authorized_keys`.
- Le dépôt est cloné en tant que `ubuntu` dans `/opt/tempo` (`sudo mkdir /opt/tempo && sudo chown ubuntu:ubuntu /opt/tempo`), puis `sudo bash bootstrap.sh <url>`, puis `sudo chown -R ubuntu:ubuntu /opt/tempo`. Les commandes `docker` se lancent avec `sudo`.
- La clé de déploiement GitHub peut être ajoutée depuis le PC: `gh repo deploy-key add tempo_deploy.pub --allow-write`.
- Gateway démarre en une minute et se connecte sans 2FA au compte paper. Si un second Gateway (PC) est connecté, IBKR le déconnecte: couper le PC d'abord.
- Le dépôt étant public, le ledger poussé par le VPS est public. `.env` et `deploy/gateway.env` ne sont jamais commités.
- Le ledger est désormais écrit par le VPS: sur le PC, faire `git pull` avant de lire `ledger/`.

## 1. Créer le serveur
1. Sur ton PC, si tu n'as pas déjà de clé SSH: `ssh-keygen -t ed25519` (Entrée partout).
2. DigitalOcean → Create → Droplets: **Ubuntu 24.04**, **Basic, Regular, 2 GiB / 1 vCPU (12 USD)**, région **New York**,
   authentification **SSH key** (colle le contenu de `C:\Users\rayya\.ssh\id_ed25519.pub`). Nom: `tempo`.
3. Note l'adresse IP. Test: `ssh root@IP`.

## 2. Donner au serveur le droit de pousser le ledger sur GitHub
Sur le serveur:
```
ssh-keygen -t ed25519 -f ~/.ssh/tempo_deploy -N ""
printf 'Host github.com\n  IdentityFile ~/.ssh/tempo_deploy\n' >> ~/.ssh/config
cat ~/.ssh/tempo_deploy.pub
```
GitHub → le repo Tempo → Settings → Deploy keys → Add: colle la clé, coche **Allow write access**. Cette clé ne donne
accès qu'à ce repo.

## 3. Installer
Depuis le PC (dans le dossier Tempo): `scp deploy/bootstrap.sh root@IP:/root/`
Sur le serveur: `bash /root/bootstrap.sh git@github.com:Rayyan-Oumlil/Tempo.git`

Le script règle l'horloge sur New York, installe Docker et Python, ferme tout sauf SSH (pare-feu), clone le repo dans
`/opt/tempo` et installe les dépendances.

## 4. Couper le PC (obligatoire avant la suite)
Dans PowerShell, dans le dossier Tempo: `powershell -ExecutionPolicy Bypass -File tools\sched\register.ps1 -Remove`
Puis ferme IB Gateway sur le PC (IBKR n'accepte qu'une session par identifiant).

## 5. Copier les secrets et l'état
Depuis le PC, dans le dossier Tempo:
```
scp .env root@IP:/opt/tempo/
scp state.json root@IP:/opt/tempo/
scp -r journal root@IP:/opt/tempo/
scp data/insider_cache.jsonl data/insider_routine.json root@IP:/opt/tempo/data/
```
Sur le serveur, crée l'identifiant Gateway (ton compte **paper**):
```
cd /opt/tempo && cp deploy/gateway.env.example deploy/gateway.env && chmod 600 deploy/gateway.env .env
nano deploy/gateway.env        # TWS_USERID, TWS_PASSWORD (paper), VNC_SERVER_PASSWORD (un mot de passe au choix)
```

## 6. Démarrer Gateway et vérifier
```
cd /opt/tempo
docker compose -f deploy/docker-compose.yml up -d
docker compose -f deploy/docker-compose.yml logs -f      # Ctrl+C pour sortir; attendre "Login has completed"
.venv/bin/python tools/readonly_check.py 4002             # doit dire PAPER
IBKR_READONLY=0 .venv/bin/python -m tempo.paper_run preflight   # aucun [FAIL]
```
Si la connexion bloque sur une fenêtre (2FA, avertissement paper): depuis le PC, `ssh -L 5900:localhost:5900 root@IP`,
puis un client VNC (TightVNC, RealVNC) sur `localhost:5900` avec le `VNC_SERVER_PASSWORD`. Clique, puis referme.

## 7. Lancer la routine
`crontab /opt/tempo/deploy/crontab` puis `crontab -l` pour vérifier (mêmes horaires que sur le PC, heure de New York).
Le soir même, `tail -50 /opt/tempo/logs/sched.log` doit montrer le job du soir.

## 8. Alertes email (gratuit, recommandé)
Compte Google → Sécurité → validation en deux étapes activée → **Mots de passe des applications** → crée-en un pour
« Tempo ». Ajoute dans `/opt/tempo/.env`:
```
TEMPO_SMTP_USER=ton.adresse@gmail.com
TEMPO_SMTP_PASSWORD=le mot de passe d'application (16 lettres)
```
Test: `cd /opt/tempo && .venv/bin/python -c "from tempo.notify import send_email; print(send_email('Tempo test', 'ok'))"` → `True`.

## Ce qui reste à surveiller
- **Connexion hebdomadaire:** IBC redémarre Gateway chaque nuit sans 2FA, mais IBKR exige une vraie connexion une fois par
  semaine (dimanche). Si ton compte paper demande une approbation 2FA, tu recevras la notification IBKR Mobile: approuve-la.
  On saura dès la première semaine si c'est le cas.
- **IBC est archivé** (dépôt en lecture seule depuis le 2026-09-01). L'image est figée sur une version qui marche; si IBKR
  change son écran de connexion, il faudra une autre solution.
- **P&L capricieux:** Gateway tourne en continu sur le VPS. On mesurera si le P&L répond mieux qu'avec les connexions du PC.

## Revenir en arrière
Sur le serveur: `crontab -r && docker compose -f /opt/tempo/deploy/docker-compose.yml down`.
Recopie `journal/` et `state.json` du serveur vers le PC (`scp -r root@IP:/opt/tempo/journal .`), puis sur le PC:
`powershell -ExecutionPolicy Bypass -File tools\sched\register.ps1`.
