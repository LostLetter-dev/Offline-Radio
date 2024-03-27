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

    audioPlayer.src = source;

    audioPlayer.addEventListener('ended', function() {
        played = false
        
        audioPlayer.src = source;
        audioPlayer.load();
        audioPlayer.play();
    });

    audioPlayer.addEventListener('play', function() {
        if (played == true) {
            audioPlayer.src = source;
            audioPlayer.load();
            played = false;
        }
    });

    audioPlayer.addEventListener('pause', function() {
        played = true;
    });
}

window.onload = function() {
    loadAudio();
};