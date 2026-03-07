# CommuneSante

**Tableau de bord de la santé financière communale – Phase 1 : Module Finances**

CommuneSante transforme les données financières publiques (DGFiP / data.gouv.fr) en indicateurs lisibles et actionnables pour piloter une commune. L'application est conçue pour les élus, les services municipaux et tout citoyen souhaitant comprendre la santé financière de sa commune.

> Commune de référence : **Sautron** (Loire-Atlantique, 44) — code INSEE `44196`

---

## Fonctionnalités

### Tableau de bord principal
- **Score de santé financière** global sur 100 avec jauge colorée et interprétation
- **6 indicateurs clés** (KPI cards) avec statut visuel (vert / orange / rouge)
- **Graphique d'évolution pluriannuelle** des recettes, dépenses et épargne brute
- **Bandeau d'alertes** actives dès qu'un indicateur dépasse un seuil critique
- **Sélecteur d'année** pour naviguer dans l'historique financier

### Indicateurs calculés

| Indicateur | Formule | Seuil d'alerte |
|---|---|---|
| Épargne brute | Recettes réelles fonct. – Dépenses réelles fonct. | < 8 % des recettes |
| Épargne nette | Épargne brute – Remboursement capital dette | < 2 % des recettes |
| Taux de rigidité des charges | (Personnel + Intérêts dette) / Recettes fonct. | > 65 % |
| Taux de fonctionnement | Dépenses réelles fonct. / Recettes réelles fonct. | > 95 % |
| Effort d'équipement | Dépenses équipement / Recettes fonct. | < 10 % |
| Dépendance aux dotations (DGF) | DGF / Recettes totales fonct. | > 25 % |

### Pages détaillées
- **Recettes** — répartition par chapitre (camembert), évolution pluriannuelle, tableau détaillé BP vs réalisé
- **Dépenses** — structure des charges (personnel, générales…), évolution des charges de personnel
- **Investissements** — volume d'équipement, sources de financement (autofinancement, emprunts, subventions, FCTVA)
- **Dette** — intérêts, remboursement capital, variation nette, évolution de l'épargne brute

### Données et synchronisation
- Collecte automatique depuis **data.gouv.fr / API DGFiP** (synchronisation hebdomadaire configurable)
- Import manuel de fichiers **PDF** de budgets primitifs (parser intégré)
- Tracabilité de chaque donnée (source : API, PDF, saisie manuelle)
- Export possible via l'API REST

---

## Architecture technique

```
Apache2 (80/443) — reverse proxy
    ├── /api/*  →  Backend FastAPI (Python 3.12) :8000
    └── /*      →  Frontend React/Vite            :3000
                        │
                   PostgreSQL 15 (interne Docker)
```

| Composant | Technologie |
|---|---|
| Backend | FastAPI (Python 3.12), SQLAlchemy 2, Alembic, APScheduler |
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS + Recharts |
| Base de données | PostgreSQL 15 |
| Conteneurisation | Docker Compose |
| Reverse proxy | Apache2 (VPS) |

---

## Installation sur VPS avec Apache2

### Prérequis

- VPS sous Debian/Ubuntu avec **ISPConfig** installé et opérationnel
- **Docker** et **Docker Compose** installés
- Un **domaine ou sous-domaine** déjà créé dans ISPConfig et pointant vers l'IP du VPS

> ISPConfig gère Apache2, les VirtualHosts et les certificats SSL via son interface web. **Ne pas créer de VirtualHost manuellement** — ISPConfig écraserait toute configuration manuelle.

---

### 1. Installer Docker

```bash
# En tant que root ou avec sudo
apt update
curl -fsSL https://get.docker.com | sh
usermod -aG docker $USER   # remplacer $USER par l'utilisateur système ISPConfig du site

# Installer Docker Compose
apt install docker-compose-plugin -y
```

Vérifier l'activation des modules Apache2 nécessaires au proxy (normalement déjà présents avec ISPConfig) :

```bash
a2enmod proxy proxy_http proxy_wstunnel headers
systemctl reload apache2
```

---

### 2. Cloner le dépôt

```bash
cd /opt
git clone https://github.com/raphaeldeux/communesante.git
cd communesante
```

---

### 3. Configurer les variables d'environnement

```bash
cp .env.example .env
nano .env
```

Renseigner au minimum :

```env
POSTGRES_PASSWORD=mot_de_passe_fort_et_unique
API_SECRET_TOKEN=token_aleatoire_32_caracteres_minimum
COMMUNE_INSEE=44196
SYNC_CRON=0 3 * * 0
```

> Pour générer un token aléatoire : `openssl rand -hex 32`

---

### 4. Lancer l'application avec Docker Compose

```bash
docker compose -f docker-compose.apache.yml up -d --build
```

Vérifier que les conteneurs sont bien démarrés :

```bash
docker compose -f docker-compose.apache.yml ps
```

Les services sont alors accessibles localement :
- Backend API : `http://127.0.0.1:8000`
- Frontend : `http://127.0.0.1:3000`

---

### 5. Configurer le reverse proxy dans ISPConfig

ISPConfig gère les VirtualHosts via son interface. La configuration proxy se fait dans le champ **"Apache Directives"** du site.

**Dans ISPConfig → Sites → Votre site → onglet "Options" → "Apache Directives" :**

```apache
# Proxy vers l'API backend (FastAPI)
ProxyPreserveHost On
ProxyPass        /api/ http://127.0.0.1:8000/
ProxyPassReverse /api/ http://127.0.0.1:8000/

# Proxy vers le frontend (React SPA)
ProxyPass        / http://127.0.0.1:3000/
ProxyPassReverse / http://127.0.0.1:3000/

# Support WebSocket
RewriteEngine On
RewriteCond %{HTTP:Upgrade} websocket [NC]
RewriteCond %{HTTP:Connection} upgrade [NC]
RewriteRule ^/?(.*) "ws://127.0.0.1:3000/$1" [P,L]
```

Cliquer sur **Enregistrer**. ISPConfig recharge Apache2 automatiquement.

---

### 6. Activer SSL (Let's Encrypt) via ISPConfig

Dans **ISPConfig → Sites → Votre site → onglet "SSL"** :

1. Cocher **SSL**
2. Cocher **Let's Encrypt**
3. Enregistrer — ISPConfig génère et installe le certificat automatiquement

La redirection HTTP → HTTPS peut être activée dans le même onglet via **"Redirect Type"** → `[R=301,L]`.

---

### 7. Charger les données initiales

Une fois l'application accessible, déclencher la première synchronisation des données DGFiP :

```bash
curl -X POST https://votre-domaine.fr/api/communes/44196/sync \
     -H "X-API-Token: VOTRE_API_SECRET_TOKEN"
```

La synchronisation s'exécute en arrière-plan. Rafraîchir l'interface après quelques secondes.

---

### 8. Vérifier l'installation

```bash
# Health check de l'API
curl https://votre-domaine.fr/api/health

# Réponse attendue :
# {"status":"ok","database":"ok","version":"1.0.0"}
```

---

## Mise à jour

```bash
cd /opt/communesante
git pull origin main
docker compose -f docker-compose.apache.yml up -d --build
```

---

## Commandes utiles

```bash
# Voir les logs en temps réel
docker compose -f docker-compose.apache.yml logs -f

# Logs du backend uniquement
docker compose -f docker-compose.apache.yml logs -f backend

# Redémarrer un service
docker compose -f docker-compose.apache.yml restart backend

# Arrêter l'application
docker compose -f docker-compose.apache.yml down

# Sauvegarder la base de données
docker compose -f docker-compose.apache.yml exec db \
  pg_dump -U communesante communesante > backup_$(date +%Y%m%d).sql
```

---

## Structure du projet

```
communesante/
├── backend/
│   ├── app/
│   │   ├── api/routes/      # Endpoints REST (communes, finances, indicateurs)
│   │   ├── models/          # Modèles SQLAlchemy (Commune, Exercice, Indicateur…)
│   │   ├── services/        # DGFiP, calcul indicateurs, synchronisation
│   │   ├── parsers/         # Parser PDF budgets primitifs
│   │   ├── schemas/         # Schémas Pydantic
│   │   ├── main.py          # Application FastAPI
│   │   └── scheduler.py     # Synchronisation automatique (APScheduler)
│   └── tests/               # Tests unitaires (indicateurs financiers)
├── frontend/
│   └── src/
│       ├── pages/           # Dashboard, Recettes, Dépenses, Investissements, Dette
│       ├── components/      # KpiCard, ScoreGauge, AlerteBanner, graphiques…
│       └── hooks/           # React Query (useScore, useFinances, useAlertes…)
├── apache/
│   └── communesante.conf    # Configuration Apache2 reverse proxy
├── nginx/
│   └── nginx.conf           # Configuration Nginx (alternative sans Apache2)
├── docker-compose.yml       # Déploiement avec Nginx intégré
├── docker-compose.apache.yml # Déploiement avec Apache2 externe
└── .env.example             # Variables d'environnement à configurer
```

---

## API REST

| Méthode | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Health check |
| GET | `/api/communes/{insee}` | Informations d'une commune |
| GET | `/api/communes/{insee}/finances` | Liste des exercices disponibles |
| GET | `/api/communes/{insee}/finances/{annee}` | Détail financier d'un exercice |
| GET | `/api/communes/{insee}/indicateurs/{annee}` | Indicateurs calculés |
| GET | `/api/communes/{insee}/score` | Score de santé financière |
| GET | `/api/communes/{insee}/alertes` | Alertes actives |
| GET | `/api/communes/{insee}/evolution` | Évolution pluriannuelle |
| POST | `/api/communes/{insee}/sync` | Synchronisation DGFiP |
| POST | `/api/communes/{insee}/import-pdf` | Import PDF budget primitif |

Documentation interactive disponible sur `/api/docs` (Swagger UI).

---

## Roadmap

| Phase | Contenu | Statut |
|---|---|---|
| Phase 1 | Module Finances (DGFiP, indicateurs, dashboard) | ✅ En cours |
| Phase 2 | Multi-communes, benchmark départemental | 🔜 Planifié |
| Phase 3 | Démographie (INSEE) | 🔜 Planifié |
| Phase 4 | Services publics (écoles, transports…) | 🔜 Planifié |
| Phase 5 | IA & prévisions financières | 🔜 Planifié |
| Phase 6 | Multi-utilisateurs, OAuth2 | 🔜 Planifié |

---

## Licence

Projet open source — données financières issues de data.gouv.fr (Licence Ouverte 2.0).
