// Aggiunge un listener che attende il completo caricamento del DOM prima di eseguire il codice.
document.addEventListener('DOMContentLoaded', async () => {
    // +++ Gestione dei messaggi flash +++
    // ottiene il contenitore dei messaggi flash ("flash-messages-container")
    const flashMessageContainer = document.getElementById('flash-messages-container');
    // verifica che il contenitore esista.
    if (flashMessageContainer) {
        // aggiunge un listener per l'evento "mouseover" (quando il mouse entra nell'area del container...)
        flashMessageContainer.addEventListener('mouseover', (event) => {
            const container = event.currentTarget;
            // ... imposta l'opacità a 0 per iniziare un effetto di dissolvenza (fade out).
            container.style.opacity = '0';
            // imposta un timeout per nascondere completamente il container dopo la dissolvenza (0.5 secondi).
            setTimeout(() => {
                container.style.display = 'none';
            }, 500);
        });
    }

    // +++ Autocomplete +++
    const partenzaInput = document.getElementById('partenza'); // ottiene l'elemento input per la stazione di partenza
    const destinazioneInput = document.getElementById('destinazione'); // ottiene l'elemento input per la stazione di destinazione
    const partenzaDataList = document.getElementById('partenza-list'); // ottiene l'elemento "<datalist>" associato alla partenza (dove verranno mostrati i suggerimenti)
    const destinazioneDataList = document.getElementById('destinazione-list'); // ottiene l'elemento "<datalist>" associato alla destinazione (dove verranno mostrati i suggerimenti)

    /**
     * Funzione per recuperare i suggerimenti di fermate dall'API Flask.
     * @param {string} query - Il testo inserito dall'utente;
     * @param {HTMLElement} datalist
     - L'elemento <datalist> dove inserire i suggerimenti.
     */
    function fetchSuggestions(query, datalist) {
        // non avvia la ricerca API, se la query è troppo corta
        if (query.length < 2) {
            datalist.innerHTML = ''; // pulisce i suggerimenti precedenti
            return;
        }
        // esegue una richiesta FETCH all'endpoint API '/api/suggest_stops' con la query.
        fetch(`/api/suggest_stops?q=${query}`) // Converte la risposta in JSON.
            .then(response => response.json())
            .then(data => {
                datalist.innerHTML = ''; // pulisce l'elenco dei suggerimenti esistenti.
                // itera sui suggerimenti ricevuti (array di nomi di fermate).
                data.forEach(suggestion => { // crea un nuovo elemento <option> per ogni suggerimento.
                    const option = document.createElement('option'); // imposta il valore dell'opzione (il nome della fermata).
                    option.value = suggestion; // aggiunge l'opzione al datalist.
                    datalist.appendChild(option);
                });
            });
    }
    // aggiunge un listener all'input di partenza per reagire a ogni battitura ('input').

    partenzaInput.addEventListener('input', (event) => {
        // chiama la funzione di recupero suggerimenti passando il valore corrente e la datalist di partenza.
        fetchSuggestions(event.target.value, partenzaDataList);
    });
    // aggiunge un listener all'input di destinazione.
    destinazioneInput.addEventListener('input', (event) => {
        // chiama la funzione di recupero dei suggerimenti per la destinazione.
        fetchSuggestions(event.target.value, destinazioneDataList);
    });

});