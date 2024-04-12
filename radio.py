# Server/System imports.

from flask import Flask, Response, render_template, request, jsonify
# For webserver ^

import threading as th
import time
import os
import io
import webbrowser as wb
import pandas as pd

#Imports for file processing

import soundfile as sf
import random as rnd
import math
import numpy as np

app = Flask(__name__, static_url_path="/static", template_folder="templates/")

# Functions here

def cutWAV(filename, startTime):
    #read WAV
    data, sampleRate = sf.read(filename)
    skippedFrames = int(startTime * sampleRate)
    
    modified = data[skippedFrames:]
    buffer = io.BytesIO()

    sf.write(buffer, modified, sampleRate, format='wav') #Write modified data to memory buffer
    buffer.seek(0)

    return buffer

def errorHandle(reason): #Lazy, but it works
    print(reason)
    print("This program will now terminate.")
    input(">")
    exit()

# Init all variables

## Init valid stations
try: stations = [path for path in os.listdir("stations/") if os.path.isdir(os.path.join("stations/", path)) == True]
except:
    errorHandle("stations/ directory does not exist")

# Remove invalid stations (stations that don't have any files)
for path in stations:
    if len([file for file in os.listdir(os.path.join("stations/", path)) if '.wav' in file ]) == 0:
        stations.remove(path)
        print(f"stations/{path} has been removed from valid stations.")
        print("This is because there are no valid .wav files in the folder, or the folder is empty.")

if len(stations) == 0:
    errorHandle("No valid stations remaining")

## Init dataframe for handling stations

df = pd.DataFrame(columns=["Station", "validFiles", "globalIndex", "globalStart", "switch", "duration"])

for path in stations:
    x = [file for file in os.listdir(os.path.join('stations/', path)) if '.wav' in file]
    x = np.array(x)
    x = x.tolist()
    rnd.shuffle(x)
    df.loc[len(df)] = {
        "Station": path,
        'validFiles': x,
        'globalIndex': 0,
        'globalStart': 0,
        'switch': True,
        'duration': 0}

tuned = df['Station'].iloc[0] #Tune into the first station available automatically.

# Multithreaded stuff down here
def updatePos():
    global df
    while True:
        
        for index, row in df.iterrows():
            switch = row['switch']

            if switch:
                with sf.SoundFile(os.path.join("stations/"+row['Station'], row['validFiles'][row['globalIndex']]), 'rb') as x:
                    df.at[index, 'duration'] = math.trunc(x.frames / x.samplerate)
                    x.close()
                    df.at[index, 'switch'] = False
            
        time.sleep(1)

        for index, row in df.iterrows():
            df.at[index, 'globalStart'] += 1
            if row['globalStart'] > row['duration']:
                df.at[index, 'globalIndex'] = (row['globalIndex'] + 1) % len(row['validFiles'])
                df.at[index, 'switch'] = True
                df.at[index, 'globalStart'] = 0

updateThread = th.Thread(target=updatePos)
updateThread.daemon = True
updateThread.start()

#Actual flask stuff.

## Main page
@app.route('/')
def index():
    return render_template("index.html")

@app.route('/stream')
def stream():
    first = True
    global tuned

    def generate(info):
        nonlocal first
        localIndex = 0
        files = np.array(info['validFiles'])
        files = files[0]

        while True:
            for index in range(len(files)):
                if first:
                    localIndex += info.iloc[0, 2] #No idea why, but calling "globalIndex" directly just doesn't work.

                    modifiedAudio = cutWAV('stations/'+info['Station'].iloc[0]+"/"+files[localIndex], info['globalStart'].iloc[0])
                    data = modifiedAudio.read(1024)
                    while data:
                        yield data
                        data = modifiedAudio.read(1024)
                    
                    first = False
                    localIndex += 1 #Necessary to sync up playback with master stream position
                    if localIndex > info.iloc[0, 2]:
                        localIndex = 0
                
                if not first:
                    with open('stations/'+info['Station'].iloc[0]+"/"+files[localIndex], 'rb') as f:
                        while True:
                            data = f.read(1024)
                            if not data:
                                break
                            yield data
                        f.close()
                
                localIndex = (localIndex + 1) % len(files)

    return Response(generate(df.loc[df['Station'] == tuned]), mimetype='audio/wav')

@app.route('/tune', methods=['POST'])
def tune():
    global df
    global tuned
    stationID = request.json.get('stationID')
    stationINF = df.loc[df['Station'] == stationID]
    if stationINF.empty:
        return Response("Station not found", status=404)
    
    tuned = stationID

    return Response(f"Tuned station to {stationID}", status=200)

@app.route('/update')
def update():
    global df

    stationNames = df['Station'].tolist()
    
    data = {str(index): item for index, item in enumerate(stationNames)} # Convert into a dictionary.
    return jsonify(data) # Send to webpage
    
    # Dynamically-updating data.
    # This is used to send every station name to the webpage.

@app.route('/updateActive')
def activeUpdate(): #Actively-updating data. Stuff people want to know.
    global df
    global tuned

    current = df.loc[df['Station'] == tuned]
    index = current['globalIndex'].iloc[0]
    files = np.array(current['validFiles'])
    files = files[0]

    currentSong = files[index]

    data = {
        "station": tuned,
        "song": currentSong
    }

    return jsonify(data)

@app.route('/kill')
def kill():
    exit() # Acts as a killswitch incase application doesn't close.
    # Revise this later - doesn't work in its current state.

wb.open("http://127.0.0.1:5000") #Points users to main webpage

if __name__ == '__main__':
    app.run(debug=True)
