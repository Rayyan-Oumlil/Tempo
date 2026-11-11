# Plan: du paper à l'argent réel (rédigé le 2026-11-10)

But: trouver **une** source de rendement qui survit aux frais à la taille réelle du compte, la prouver sans se mentir, puis
la trader avec de l'argent réel en petit, sur une infrastructure qui ne dépend ni du PC ni d'une surveillance constante.

Ce plan ne promet pas de gain. Il promet que **si** un gain existe dans ce qu'on peut tester, on le verra vite, et que
s'il n'existe pas, on ne perdra pas d'argent réel à le découvrir.

## 0. Où on en est (faits, 2026-11-10)

| | État |
|---|---|
| Backtests pré-enregistrés | 6 sur 6 ratés (SMA 200, momentum, paires, overnight, mean reversion, allocation tactique) |
| Tests en avant | insiders `insider_cluster_v1` (46 signaux, 1 jour: n=35, +0,20 %, t=0,37); lecture des résultats `claude_earnings_v1` (10 signaux, 1 jour: -1,83 %, t=-1,36); mean reversion (aucun trade) |
| Paper | 20 positions insiders, sortie le 2026-12-08 |
| Infrastructure | Porte d'ordres, journal, kill switch, scheduler Windows, garde P&L. Dépend du PC et d'un login Gateway manuel |
| Capital réel connu | Compte live de ton père: 3 000 USD |

**Ce qui est subtil:** un test à 100 signaux ne détecte que de gros effets. Avec un écart-type de ~12 % par trade sur
21 jours (petites capitalisations; c'est une estimation), il faut un excès moyen de ~2,4 % par trade pour atteindre t=2.
Un effet réaliste de ~0,8 %/mois demanderait de l'ordre de 900 signaux. Conclusion: **il faut plus de signaux par
semaine, pas seulement plus de patience.**

## 1. Garde-fous avant tout (cette semaine)

Ces points peuvent coûter plus cher qu'une mauvaise stratégie.

| # | Action | Pourquoi |
|---|---|---|
| 1.1 | **Vérifier la politique de transactions personnelles de la Banque Nationale** (pré-approbation, liste restreinte, période de détention minimale, comptes « sous influence », y compris celui de ton père) | Ton objectif #1 est un poste permanent là-bas. Beaucoup de banques imposent une pré-approbation et une détention minimale (souvent 30 jours), ce qui rendrait impossibles les horizons 1 à 5 jours. `gate.json` l'exige déjà |
| 1.2 | Permis d'études et fiscalité (déjà dans `gate.json`); fiscalité du compte au Qatar pour la personne qui trade | Une stratégie gagnante ne vaut rien si elle met le statut en danger |
| 1.3 | Accès officiel au compte de ton père (autorisation de trading IBKR), pas de partage de mot de passe | Conditions d'IBKR et responsabilité |
| 1.4 | Garde « compte attendu » dans Tempo (`IBKR_ACCOUNT`), avec tests | Aujourd'hui n'importe quel compte DU* passe; c'est arrivé ce soir |
| 1.5 | Commiter le scheduler et les outils de lecture seule; alertes par email | Une alerte popup ratée = une journée perdue |

## 2. Élargir l'entonnoir: plusieurs signaux en parallèle, chacun pré-enregistré

Principe: chaque idée a un fichier `evidence/*.json` écrit **avant** le premier signal (règle, horizon, coût supposé,
critère de succès, critère d'abandon). Le ledger les score tous. On ne retouche jamais une règle après avoir vu des
résultats; on crée une v2 à côté.

| Signal | Données (gratuites) | Ressource IBKR | Ce que dit la littérature | Quand |
|---|---|---|---|---|
| A. Insiders **opportunistes** `insider_opportunistic_v2`: exclure les initiés « de routine » (achats le même mois plusieurs années de suite) | SEC Form 4 (déjà collecté) + historique des initiés (data sets SEC trimestriels, depuis 2006) | Barres journalières, scanner pour la liquidité | Cohen-Malloy-Pomorski: opportunistes ~82 pb/mois, routine ~0 (échantillon jusqu'en 2007). Contre: l'effet disparaît à taille réaliste et avec la liquidité (déjà noté dans `insider_forward.json`) | Novembre |
| B. **Dérive post-résultats** (PEAD) sur la réaction de prix seulement, sans LLM | Dates 8-K 2.02 (EDGAR) | Barres journalières (gap et volume du jour de l'annonce) | Anomalie classique, affaiblie depuis sa publication | Construire en décembre, saison de résultats mi-janvier 2027 |
| C. **Lecture des résultats par Claude** à l'échelle (au-delà des 10 du pilote) | Communiqués 8-K | — | Lopez-Lira et Tang, Kim-Muhn-Nikolaev: positif mais risque de mémorisation; le test en avant l'évite | Saison de janvier; demande un **plafond de dépenses API** de ta part |
| D. **Titres de nouvelles** notés par LLM (petites caps, nouvelles négatives) | — | Nouvelles Briefing.com / Dow Jones par défaut dans l'API (**contenu jamais testé**) | Lopez-Lira et Tang | D'abord vérifier que le contenu arrive (1 h de test) |
| E. Mean reversion (déjà en cours) | — | Barres journalières | Survit aux frais, ne bat pas l'index depuis 2010 | Continue tel quel |

**Ce qui est subtil:** plus on teste de signaux, plus l'un d'eux gagnera par chance. On pré-enregistre une correction
(par exemple Bonferroni sur le nombre de sources actives) avant le premier score.

## 3. Mesurer comme si c'était de l'argent réel

| # | Action |
|---|---|
| 3.1 | Modèle de frais **par taille de compte**: commission IBKR fixe (0,005 USD/action, min. 1 USD) + écart estimé. Le ledger affiche le résultat net pour 3 000, 25 000 et 100 000 USD. Chaque stratégie reçoit un **capital minimum viable** |
| 3.2 | Mesurer le vrai écart de prix: `whatIf` donne la commission; la cote différée suffit pour des barres journalières. Le temps réel (~10 USD/mois, annulé à 30 USD de commissions; prix à confirmer) n'est utile qu'en phase 5 (`gate.json` exige 2 semaines de temps réel) |
| 3.3 | Rapport mensuel: par source, n, moyenne nette, t, intervalle de confiance, et « signaux nécessaires pour conclure » |

## 4. Infrastructure prête pour le réel (en parallèle, décembre)

| # | Action | Ressource |
|---|---|---|
| 4.1 | VPS (~12 USD/mois, DigitalOcean 2 GiB) avec Gateway en Docker (IBC) et un **processus qui garde la connexion ouverte** | Règle probablement le P&L capricieux (le premier essai après connexion répond, les suivants non) |
| 4.2 | Configuration live séparée: port 4001, compte épinglé, journal et état distincts, limites en dollars (et pas en %) | |
| 4.3 | **Mode ombre** sur le compte live, en lecture seule: Tempo calcule chaque jour ce qu'il ferait, sans rien envoyer | MCP officiel ou script en lecture seule |
| 4.4 | Premiers ordres réels **mis en attente par l'API et approuvés à la main sur l'appli mobile** | API 10.43 (staging mobile) |
| 4.5 | Vérifier « Enable ActiveX and Socket Clients » après chaque mise à jour de Gateway | Changement de la 10.45 |
| 4.6 | Question 2FA: la connexion live hebdomadaire demande l'approbation du titulaire | À régler avec le login officiel (1.3) |

## 5. La porte vers l'argent réel

On ne passe que si **tout** est vrai:

1. Les points 1.1 à 1.3 sont réglés par écrit.
2. Une source passe son critère pré-enregistré, **net de frais à la taille réelle du compte**, après la correction pour tests multiples.
3. Le paper suit le ledger (même signe, écart expliqué) sur au moins 60 jours de trading (`gate.json`).
4. Quatre semaines d'exploitation automatique sans incident non expliqué (`max_process_error_share` 5 %).
5. Le mode ombre live colle au paper pendant 2 semaines.

Ensuite: **petite taille, approbation manuelle de chaque ordre**. On double la taille après 20 trades si le réel suit le
paper. Arrêt immédiat si la perte dépasse un montant fixé à l'avance, ou si le réel s'écarte du paper au-delà d'une
limite fixée à l'avance.

## 6. Calendrier réaliste

| Quand | Quoi |
|---|---|
| Semaine du 10 nov. | Phase 1 (garde-fous), test des nouvelles (D) |
| Novembre | Signal A pré-enregistré et lancé; modèle de frais (3.1) |
| Décembre | VPS et connexion persistante (4.1-4.3); signal B prêt; 8 déc.: premières sorties et scores à 21 jours |
| Mi-janvier à février 2027 | Saison des résultats: B et C produisent du volume |
| ~Février-mars 2027 | Premier verdict possible pour les insiders (assez de scores à 21 jours) et premières lectures pour B/C |
| Au plus tôt ~mars 2027 | Première décision « argent réel », si la porte (section 5) est franchie |

## 7. Décisions qui t'appartiennent

1. Contacter la conformité de la Banque Nationale (bloquant).
2. Le plafond de dépenses API pour la lecture des résultats par Claude (signal C).
3. VPS: oui ou non (~12 USD/mois).
4. Le capital réel envisagé, qui décide quelles stratégies sont même viables (section 3.1).

## Sources
- Cohen, Malloy, Pomorski, Decoding Inside Information: https://www.nber.org/papers/w16454
- Notes de version 2026 de l'API TWS: https://www.ibkrguides.com/releasenotes/prod-2026.htm
- Nouvelles et scanners de l'API: https://interactivebrokers.github.io/tws-api/news.html, https://interactivebrokers.github.io/tws-api/market_scanners.html
- Biais « look-ahead » des LLM: https://arxiv.org/pdf/2601.13770 ; critique de l'alpha des agents: https://arxiv.org/pdf/2605.16895
- Recherche antérieure du projet: docs/research/what-people-do.md, docs/ibkr-gotchas.md, evidence/gate.json
