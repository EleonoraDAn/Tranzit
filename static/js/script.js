document.addEventListener('DOMContentLoaded', async () => {
    const flashMessageContainer = document.getElementById('flash-messages-container');
    if (flashMessageContainer) {
        flashMessageContainer.addEventListener('mouseover', (event) => {
            const container = event.currentTarget;
            container.style.opacity = '0';
            setTimeout(() => {
                container.style.display = 'none';
            }, 500);
        });
    }

    const partenzaInput = document.getElementById('partenza');
    const destinazioneInput = document.getElementById('destinazione');
    const partenzaDataList = document.getElementById('partenza-list');
    const destinazioneDataList = document.getElementById('destinazione-list');

    function fetchSuggestions(query, datalist) {
        if (query.length < 2) {
            datalist.innerHTML = '';
            return;
        }
        fetch(`/api/suggest_stops?q=${query}`)
            .then(response => response.json())
            .then(data => {
                datalist.innerHTML = '';
                data.forEach(suggestion => {
                    const option = document.createElement('option');
                    option.value = suggestion;
                    datalist.appendChild(option);
                });
            });
    }

    partenzaInput.addEventListener('input', (event) => {
        fetchSuggestions(event.target.value, partenzaDataList);
    });

    destinazioneInput.addEventListener('input', (event) => {
        fetchSuggestions(event.target.value, destinazioneDataList);
    });

});