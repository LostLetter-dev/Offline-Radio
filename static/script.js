function updateDynamic() {
    fetch('/updateActive')
        .then(response => response.json())
        .then(data => {
            console.log("Received data:", data);
            document.getElementById('station').innerText = data.station || 'N/A';
            document.getElementById('song').innerText = data.song || 'N/A';
        });
}

function loadAudio() {
    const source = "http://127.0.0.1:5000/stream";
    const audioContainer = document.getElementById('audioContainer');
    const audioPlayer = document.createElement('audio');
    audioPlayer.id = 'audioPlayer';
    audioPlayer.controls = true;
    audioPlayer.controlslist = 'nodownload';
    audioPlayer.innerHTML = "Your browser does not support the audio element.";
    audioContainer.appendChild(audioPlayer);
    // Creates audio player.

    var played = false

    audioPlayer.src = source;

    audioPlayer.addEventListener('ended', function() {
        played = false
        
        audioPlayer.src = source;
        audioPlayer.load();
        updateDynamic();
        audioPlayer.play();
    });

    audioPlayer.addEventListener('play', function() {
        if (played == true) {
            audioPlayer.src = source;
            audioPlayer.load();
            played = false;
            updateDynamic();
        }
    });

    audioPlayer.addEventListener('pause', function() {
        played = true;
    });
}


function postData(data) { // Sends information off to the program.
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/tune", true);
    xhr.setRequestHeader("Content-Type", "application/json");

    // Data to be sent
    var data = JSON.stringify({"stationID": data});

    xhr.onreadystatechange = function () {
    if (xhr.readyState === 4 && xhr.status === 200) {
        console.log("Tuning successful!");
        }
    };

xhr.send(data);
document.getElementById('audioPlayer').load()
updateDynamic();
}

function stationList() {
    fetch('/update')
        .then(response => response.json())
        .then(data => {
            // Recursively add new buttons for each station.
            content = document.getElementById('stations')
            content.innerHTML = ''; // Clear everything in the divider.

            // Iterate
            Object.keys(data).forEach(key => {
                // Create buttons
                var button = document.createElement('button');
                button.innerHTML = data[key];

                button.addEventListener('click', function() {
                    postData(data[key]);
                });
                
                content.appendChild(button);
            });
        });
}

window.onload = function() { // Happens when the webpage loads.
    loadAudio();
    stationList();
    updateDynamic();
};
