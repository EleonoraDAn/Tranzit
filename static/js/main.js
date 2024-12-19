if ('serviceworker' in navigator) {
    navigator.serviceWorker.register('/static/js/sw.js')
    .then((reg) => console.log('serivce worker registered', reg))
    .catch((err) => console.log('serivce worker registration error:', err))
}

/* function clickButton(event) {
    event.preventDefault();
    let partenza = document.getElementById("partenza").value.trim();
    let destinazione  = document.getElementById("destinazione").value.trim();
    partenza = partenza.replace(/\s+/g, '_').toLowerCase();
    destinazione = destinazione.replace(/\s+/g, '_').toLowerCase();
    const url = 'https://www.e656.net/orario/collegamenti/${partenza}/${destinazione}.html';
    window.open(url, '_blank');
    document.getElementById('ottieniBiglietti').addEventListener("submit", clickButton);
}
 const input = document.getElementById("partenza");
const suggestions = document.getElementById("partenzaSuggestions");
let stations = [];


fetch('stazioni.json')
    .then(response => response.json())
    .then(data => {
        stations = data;
    })
    .catch(error => console.error('Errore nel carimento delle stazioni:', error));


input.addEventListener("input", () => {
    const query = input.value.toUpperCase();
    suggestions.innerHTML = ""; // Pulire i suggerimenti

    if (query) {
        const filteredStations = stations.filter(station => station.toLowerCase().includes(query));

        filteredStations.forEach(station => {
            const suggestionDiv = document.createElement("div");
            suggestionDiv.textContent = station;
            suggestionDiv.addEventListener("click", () => {
                input.value = station;
                suggestions.innerHTML = ""; // Chiudi i suggerimenti
            });
            suggestions.appendChild(suggestionDiv);
        });
    }
});

// Chiudi suggerimenti quando si clicca fuori
document.addEventListener("click", (event) => {
    if (!suggestions.contains(event.target) && event.target !== input) {
        suggestions.innerHTML = ""; // Chiudi i suggerimenti
    }
});
*/
function cercaBiglietto(codtreno){
    window.open(`https://m.e656.net/orario/treno/${codtreno}.html`)
}