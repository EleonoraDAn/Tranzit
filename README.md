# Tranzit

# --- IN INGLESE ---

# Web Tecnologies Project 
**University of Naples "Parthenope"**<br>
**Degree Course in Computer Science**<br>
**Academic Year: 2024/2025**

# Group Members 
- D'Aniello Eleonora, MAT: **0124002790**
- Alessi Lucia, MAT: **0124002496**
- Incoronato Mattia, MAT: **0124002664**

# 1. Introduction
It is a full-stack web application designed for the **search and consultation of train and bus tickets.**<br>
The goal is to create a platform that is intuitive and simple, but above all, responsive and dynamic!

# 2. System Architecture
The application follows a **three-tier** architecture:<br>
**Tranzit**: is a full-stack application developed with:
- **BACKEND**: implemented in Python using the "Flask" framework, which manages routes, application logic, and communication with the database;
- **DATABASE**: based on MongoDB Atlas, used to store information related to: routes, purchased tickets, and registered users;
- **FRONTEND**: built with HTML, CSS3, and Javascript, with dynamic templating Jinja 2 for page generation.

# 3. Tecnologies and Tools used
| Layer               | Tecnologies / Tools            |
|---------------------|--------------------------------|
| **Frontend**        | HTML, CSS3, Javascript, Jinja2 |
| **Backend**         | Python, Flask                  |
| **Database**        | MongoDB Atlas                  |
| **Version Control** | Github, Git                    |
| **Other**           | JSON, REST API                 |

# 4. Project Structure
Tranzit/<br>
|<br>
|-- app.py (Flask application entry point)<br>
|-- templates/ (HTML, Jinja 2 templates)<br>
|-- static/ (contains CSS3 files, javascript files, and the application's background image)<br>

# 5. Implemented Features 
- Search for train and bus routes;
- Search for a train/bus route by entering the journey code;
- Search for tickets by filtering by departure date and time, considering a departure and destination location (all information entered by the user via HTML form);
- If the travel date is the current date, tickets are searched with a time **EQUAL TO** or **LATER THAN** the one registered by the system;
- Consultation of notices related to railway lines and bus routes by checking the circulation websites offered by "EAV". <br>
**Railway Lines**: https://www.eavsrl.it/infomobilita-ferrovia/ <br>
**Bus Routes**: https://www.eavsrl.it/avvisi-infomobilita-autolinee/ <br>
- Registration/login system that allows viewing already booked tickets (in the "Miei Viaggi" section visible **ONLY** if logged in);
- Modification of access information (email, password, and username) via a sidebar visible **ONLY** to registered users;
- When selecting departure and destination locations, dropdown menus are shown with all stations registered in the database that start with the letters entered by the user.<br>
These options are selectable.

# 6. Data Sources (Open Data)
The project relies on publicly available data through **open data** platforms. These resources allow access to updated and structured information on public transport, in compliance with the principles of transparency and data reuse. <br>
The main sources used are:
- **Campania Region Open Dats Portal** -- information on local public transport lines, stops, and schedules;
- **GTFS (General Transit Feed Specification)** -- open standard for representing transit data (schedules, routes, stops).
The datasets were downloaded, cleaned, and imported into the **MongoDB Atlas** database to allow user-side search and consultation.

# 7. Application Screenshot
Below is a preview of the main interface of Tranzit:
![Screenshot homepage](static/img/screenshot_homepage.png)

# 8. Demo video 
A video demo is available at this link for an overview of the application's usage:
https://youtu.be/DrKreUUARDw

# --- IN ITALIANO ---
# Web Tecnologies Project
**Università degli studi di Napoli "Parthenope"**<br>
**Corso di Laurea in Informatica**<br>
**Anno accademico: 2024/2025**

## Membri del gruppo
- D'Aniello Eleonora, MAT: **0124002790**
- Alessi Lucia, MAT: **0124002496**
- Incoronato Mattia, MAT: **0124002664**

# 1. Introduzione
È un'applicazione web full-stack progettata per la **ricerca e la consultazione dei biglietti relativi a treni e bus**.<br> 
L'obiettivo è quello di realizzare una piattaforma che sia intuitiva e semplica, ma soprattutto responsiva e dinamica!

# 2. Archittettura del sistema
L'applicazione segue un'architettura di **tre livelli**:<br>
**Tranzit**: è un'applicazione full-stack sviluppata con:
- **BACKEND**: implementato in Python utilizzando il framework "Flask",che gestisce le rotte, le logiche applicative e le comunicazioni con il database;
- **DATABASE**: basato su MongoDB Atlas, utilizzato per memorizzare le informazioni relative: alle corse, ai biglietti acquistati e agli utenti registrati;
- **FRONTEND**: realizzato con HTML, CSS3 e Javascript, con templating dinamico Jinja 2 per la generazione delle pagine. 

# 3. Tecnologie e strumenti utilizzati
| Livello                   | Tecnologie / Strumenti         |
|---------------------------|--------------------------------|
| **Frontend**              | HTML, CSS3, Javascript, Jinja2 |
| **Backend**               | Python, Flask                  |
| **Database**              | MongoDB Atlas                  |
| **Controllo di versione** | Github, Git                    |
| **Altro**                 | JSON, REST API                 |

# 4. Struttura del progetto
Tranzit/<br>
|<br>
|-- app.py (entry point dell'applicazione Flask)<br>
|-- templates/ (template HTML, Jinja 2)<br>
|-- static/ (contiene file CSS3, file javascript e l'immagine di background dell'applicazione)<br>

# 5. Funzionalità implementate
- Ricerca di corse ferroviarie e relative ai bus;
- Ricerca del tragitto di un treno/bus tramite l'inserimento del codice della corsa;
- Ricerca del biglietto filtrando data e ora di partenza, considerando un luogo di partenza e di destinazione (sono tutte informazioni inserite dall'utente tramite form HTML);
- Se la data di viaggio è quella corrente, vengono ricercati i biglietti con un'orario **UGUALE** o **SUCCESSIVO** a quello registrato dal sistema;
- Consultazione degli avvisi relativi alle linee ferroviarie e autolinee tramite il consulto dei siti relativi alla circolazione offerti da "EAV". <br>
**Linee ferroviarie**: https://www.eavsrl.it/infomobilita-ferrovia/ <br>
**Autolinee**: https://www.eavsrl.it/avvisi-infomobilita-autolinee/ <br>
- Sistema di registrazione/accesso che consente la visione dei biglietti già prenotati (nella sezione "Miei Viaggi" visibile **SOLO** se è stato effettuato l'accesso);
- Modifica delle informazioni di accesso(email, password e username) tramite una sidebar visibile **SOLO** alle persone registrate;
- Quando si selezionano le località di partenza e di destinazione, vengono mostrati dei menù a tendina con tutte le stazioni registrate nel database che hanno, come iniziali, le lettere inserite dall'utente. Queste opzioni sono selezionabili.

# 6. Fonti dei dati (Open Data)
Il progetto si basa su dati pubblicamente disponibili attraverso piattaforme di **open data**.  
Tali risorse permettono di accedere a informazioni aggiornate e strutturate sui trasporti pubblici, nel rispetto dei principi di trasparenza e riuso dei dati.

Le principali fonti utilizzate sono:

- **Portale Open Data Regione Campania** – informazioni su linee, fermate e orari del trasporto pubblico locale.  
- **GTFS (General Transit Feed Specification)** – standard aperto per la rappresentazione dei dati di transito (orari, percorsi, fermate).

I dataset sono stati scaricati, puliti e importati nel database **MongoDB Atlas** per consentire la ricerca e la consultazione lato utente.

# 7. Screenshot dell'applicazione
Di seguito un'anteprima dell'interfaccia principale di **Tranzit**:
![Screenshot homepage](static/img/screenshot_homepage.png)

# 8. Video dimostrativo
Per una paronamica sull'utilizzo dell'applicazione è disponibile una demo video a questo link:
https://youtu.be/DrKreUUARDw
