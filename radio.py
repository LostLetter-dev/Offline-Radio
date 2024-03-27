# Server/System imports.

from flask import Flask, Response
import threading as th
import time
import os
import io

#Imports for file processing.
import soundfile as sf
import random as rnd
import math

# Init Flask app.
app = Flask(__name__)

# Init all variables

#audioFiles = ["1.wav", "2.wav", "4.wav", "5.wav"] #TODO make this dynamic
audioFiles = os.listdir('playlist/')
audioFiles = [file for file in audioFiles if '.wav' in file] #Filters audioFiles specifically for .wav files.
rnd.shuffle(audioFiles) #Shuffles playlist automatically.

globalStart = 0
globalIndex = 0

print(f"Starting file: {audioFiles[globalIndex]}")

#Multithreaded / async stuff down here.

def updatePos():
    global globalStart, globalIndex
    switch = True
    while True:

        if switch:
            with sf.SoundFile('playlist/'+audioFiles[globalIndex], 'rb') as x:
                duration = math.trunc(x.frames / x.samplerate)
                x.close()
                switch = False

        time.sleep(1)
        globalStart += 1
        if globalStart > duration:
            globalIndex = (globalIndex + 1) % len(audioFiles)
            switch = True
            globalStart = 0
            print(f"Switched to file: {audioFiles[globalIndex]}")

updateThread = th.Thread(target=updatePos)
updateThread.daemon = True
updateThread.start()

#Functions here.

def cutWAV(filename, startTime):
    #read WAV
    data, sampleRate = sf.read(filename)
    skippedFrames = int(startTime * sampleRate)

    modified = data[skippedFrames:] #Adjust audio data to start from spec.
    buffer = io.BytesIO()

    sf.write(buffer, modified, sampleRate, format='wav') #Write modified data to memory buffer
    buffer.seek(0) # Reset buffer position back to the beginning.

    return buffer

#Actual flask stuff. 

## Main page
@app.route('/')
def index():
    return "Welcome to the offline radio. This is the multifile startpoint test."

@app.route('/stream')
def stream():
    """Everything here acts as an init before the generate function is called."""
    first = True


    def generate():
        nonlocal first
        global globalIndex
        localIndex = 0
        
        while True:
            for index in range(len(audioFiles)):
                if first:
                    localIndex += globalIndex

                    modifiedAudio = cutWAV('playlist/'+audioFiles[localIndex], globalStart)
                    data = modifiedAudio.read(1024)
                    while data:
                        yield data
                        data = modifiedAudio.read(1024)
                    
                    first = False
                    localIndex += 1 #Necessary to sync up playback with master stream position
                
                if not first:
                    with open('playlist/'+audioFiles[localIndex], 'rb') as f:
                        while True:
                            data = f.read(1024)
                            if not data:
                                break
                            yield data
                        f.close()

                localIndex = (localIndex + 1) % len(audioFiles)
            
        
    return Response(generate(), mimetype='audio/wav')

@app.route('/kill')
def kill():
    exit() #Acts as a killswitch if the application doesn't close.

if __name__ == '__main__':
    app.run(debug=True)

## This code runs correctly. Do not edit, instead make a new project file.
